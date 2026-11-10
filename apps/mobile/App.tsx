import React, { useState, useEffect } from 'react';
import 'react-native-url-polyfill/auto';
import { createClient, type Session } from '@supabase/supabase-js';
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ScrollView,
  Modal
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import * as SecureStore from 'expo-secure-store';
import * as Crypto from 'expo-crypto';

// =============================================================================
// Global Error Boundary — prevents white screen on unhandled render errors
// =============================================================================
interface ErrorBoundaryState { hasError: boolean; error: Error | null; }
class ErrorBoundary extends React.Component<{children: React.ReactNode}, ErrorBoundaryState> {
  constructor(props: {children: React.ReactNode}) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    // Replace with Sentry or similar error tracker in production
    console.error('[ErrorBoundary] Unhandled error:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#090d16', justifyContent: 'center', alignItems: 'center', padding: 24 }}>
          <Text style={{ color: '#ef4444', fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>Something went wrong</Text>
          <Text style={{ color: '#94a3b8', fontSize: 13, textAlign: 'center' }}>
            {this.state.error?.message ?? 'An unexpected error occurred.'}
          </Text>
        </SafeAreaView>
      );
    }
    return this.props.children;
  }
}

// Wrapped export with global error boundary
const AppWithBoundary: React.FC = () => (
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);

// Security constants
const VAULT_PIN_STORAGE_KEY = 'cognix_vault_pin_hash';
const VAULT_PIN_SALT_KEY = 'cognix_vault_pin_salt';
const VAULT_LOCKOUT_KEY = 'cognix_vault_lockout_until';
const SECRET_RECORD_INDEX_KEY = 'cognix_secret_record_index_v1';
const SECRET_RECORD_LIMIT = 40;
const VAULT_PIN_MAX_ATTEMPTS = 5;
const VAULT_LOCKOUT_MS = 15 * 60 * 1000; // 15 minutes
const OFFLINE_CAPTURE_QUEUE_KEY = 'cognix_offline_capture_queue_v1';

/**
 * Native Expo crypto works on Android and iOS; browser WebCrypto is not
 * guaranteed to exist in an Expo runtime.  The PIN is additionally guarded
 * by hardware-backed SecureStore and the persisted attempt lockout below.
 */
const PIN_HASH_VERSION = 'v2';

async function generateSecureRandomSalt(): Promise<string> {
  const randomBytes = await Crypto.getRandomBytesAsync(16);
  return Array.from(randomBytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function hashPin(pin: string, salt: string): Promise<string> {
  const digest = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA512,
    `${PIN_HASH_VERSION}:${salt}:${pin}`,
  );
  return `${PIN_HASH_VERSION}:${digest}`;
}

function secureHashEquals(left: string, right: string): boolean {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

function vaultStorageKey(baseKey: string, userId: string): string {
  return `${baseKey}:${userId}`;
}

async function isVaultPinSet(userId: string): Promise<boolean> {
  const pinHashKey = vaultStorageKey(VAULT_PIN_STORAGE_KEY, userId);
  const pinSaltKey = vaultStorageKey(VAULT_PIN_SALT_KEY, userId);
  let storedHash = await SecureStore.getItemAsync(pinHashKey);
  if (!storedHash) {
    const legacyHash = await SecureStore.getItemAsync(VAULT_PIN_STORAGE_KEY);
    const legacySalt = await SecureStore.getItemAsync(VAULT_PIN_SALT_KEY);
    if (legacyHash && legacySalt) {
      await SecureStore.setItemAsync(pinHashKey, legacyHash);
      await SecureStore.setItemAsync(pinSaltKey, legacySalt);
      await SecureStore.deleteItemAsync(VAULT_PIN_STORAGE_KEY);
      await SecureStore.deleteItemAsync(VAULT_PIN_SALT_KEY);
      storedHash = legacyHash;
    } else {
      return false;
    }
  }

  // Preserve migrated verifier compatibility; the PIN hash itself protects
  // only the UI gate. Private record contents are encrypted by OS SecureStore.
 const storedSalt = await SecureStore.getItemAsync(pinSaltKey);
  if (!storedSalt) {
    await SecureStore.deleteItemAsync(pinHashKey);
    return false;
  }
  return true;
}

async function validateVaultPin(pin: string, userId: string): Promise<boolean> {
  const pinHashKey = vaultStorageKey(VAULT_PIN_STORAGE_KEY, userId);
  const pinSaltKey = vaultStorageKey(VAULT_PIN_SALT_KEY, userId);
  const storedHash = await SecureStore.getItemAsync(pinHashKey);
  if (!storedHash) return false;

  // A missing salt means this data predates the secure on-device vault format.
  // It is deliberately not accepted because the old WebCrypto-only hash could
  // not be evaluated reliably in native Expo clients.
  const storedSalt = await SecureStore.getItemAsync(pinSaltKey);
  if (!storedSalt) return false;

  const inputHash = await hashPin(pin, storedSalt);
  return secureHashEquals(inputHash, storedHash);
}

async function setVaultPin(pin: string, userId: string): Promise<void> {
  const randomSalt = await generateSecureRandomSalt();
  const hash = await hashPin(pin, randomSalt);
  await SecureStore.setItemAsync(vaultStorageKey(VAULT_PIN_SALT_KEY, userId), randomSalt);
  await SecureStore.setItemAsync(vaultStorageKey(VAULT_PIN_STORAGE_KEY, userId), hash);
}

const API_BASE = (process.env.EXPO_PUBLIC_COGNIX_API_URL || '').replace(/\/$/, '');
const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '';
const AUTH_STORAGE_CHUNK_SIZE = 1500;
const secureSessionStorage = {
  getItem: async (key: string): Promise<string | null> => {
    const countValue = await SecureStore.getItemAsync(`${key}:chunk-count`);
    if (!countValue) return SecureStore.getItemAsync(key); // Read legacy single-item sessions.
    const count = Number.parseInt(countValue, 10);
    if (!Number.isFinite(count) || count < 1 || count > 20) return null;
    const chunks = await Promise.all(
      Array.from({ length: count }, (_, index) => SecureStore.getItemAsync(`${key}:chunk:${index}`)),
    );
    if (chunks.some((chunk) => chunk === null)) return null;
    return chunks.join('');
  },
  setItem: async (key: string, value: string): Promise<void> => {
    const previousCountValue = await SecureStore.getItemAsync(`${key}:chunk-count`);
    const previousCount = Number.parseInt(previousCountValue || '0', 10);
    const count = Math.ceil(value.length / AUTH_STORAGE_CHUNK_SIZE) || 1;
    if (count > 20) throw new Error('Auth session payload exceeds secure storage capacity.');
    for (let index = 0; index < count; index += 1) {
      await SecureStore.setItemAsync(`${key}:chunk:${index}`, value.slice(index * AUTH_STORAGE_CHUNK_SIZE, (index + 1) * AUTH_STORAGE_CHUNK_SIZE));
    }
    await SecureStore.setItemAsync(`${key}:chunk-count`, String(count));
    for (let index = count; index < previousCount; index += 1) {
      await SecureStore.deleteItemAsync(`${key}:chunk:${index}`);
    }
    await SecureStore.deleteItemAsync(key);
  },
  removeItem: async (key: string): Promise<void> => {
    const countValue = await SecureStore.getItemAsync(`${key}:chunk-count`);
    const count = Number.parseInt(countValue || '0', 10);
    await SecureStore.deleteItemAsync(`${key}:chunk-count`);
    for (let index = 0; index < count && index < 20; index += 1) {
      await SecureStore.deleteItemAsync(`${key}:chunk:${index}`);
    }
    await SecureStore.deleteItemAsync(key);
  },
};
const supabaseMobile = SUPABASE_URL && SUPABASE_ANON_KEY
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        storage: secureSessionStorage,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false,
      },
    })
  : null;

interface BookItem {
  id: string;
  title: string;
  author?: string;
  chunk_count: number;
  category?: string;
  summary?: string;
}

interface SecretRecord {
  id: string;
  title: string;
  content: string;
  created_at: string;
}

interface CapturedNote {
  id: string;
  content: string;
  tag: string;
  created_at: string;
}

interface QueuedCapture extends CapturedNote {
  queued_at: string;
}

async function readOfflineCaptureQueue(userId: string): Promise<QueuedCapture[]> {
  const raw = await SecureStore.getItemAsync(`${OFFLINE_CAPTURE_QUEUE_KEY}:${userId}`);
  if (!raw) return [];
  try {
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((item): item is QueuedCapture => Boolean(item && typeof item === 'object' && typeof (item as QueuedCapture).content === 'string')) : [];
  } catch {
    return [];
  }
}

async function writeOfflineCaptureQueue(userId: string, queue: QueuedCapture[]): Promise<void> {
  // Keep pending content partitioned by account to prevent cross-owner sync.
  // This is deliberately capped: SecureStore is for small queued metadata,
  // not a general document store. The newest captures are preserved.
  await SecureStore.setItemAsync(`${OFFLINE_CAPTURE_QUEUE_KEY}:${userId}`, JSON.stringify(queue.slice(-40)));
}

interface Flashcard {
  id: string;
  question: string;
  answer: string;
  source: string;
  repetition: number;
  interval_days: number;
  ease_factor: number;
}

function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [authLoading, setAuthLoading] = useState<boolean>(true);
  const [authEmail, setAuthEmail] = useState<string>('');
  const [authPassword, setAuthPassword] = useState<string>('');
  const [authBusy, setAuthBusy] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'capture' | 'vault' | 'learn' | 'secret'>('capture');
  const [books, setBooks] = useState<BookItem[]>([]);
  const [notes, setNotes] = useState<CapturedNote[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [quickInput, setQuickInput] = useState<string>('');
  const [selectedTag, setSelectedTag] = useState<string>('#idea');
  const [offlineQueue, setOfflineQueue] = useState<QueuedCapture[]>([]);
  const [syncingQueue, setSyncingQueue] = useState(false);

  // Owner-scoped flashcards loaded from the persisted SM-2 schedule.
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [currentCardIndex, setCurrentCardIndex] = useState<number>(0);
  const [showAnswer, setShowAnswer] = useState<boolean>(false);

  // Secret Vault PIN - secure implementation
  const [secretUnlocked, setSecretUnlocked] = useState<boolean>(false);
  const [pinInput, setPinInput] = useState<string>('');
  const [pinAttempts, setPinAttempts] = useState<number>(0);
  const [vaultLocked, setVaultLocked] = useState<boolean>(false);
  const [vaultLockoutUntil, setVaultLockoutUntil] = useState<number | null>(null);
  const [vaultPinSet, setVaultPinSet] = useState<boolean | null>(null); // null = loading
  const [showPin, setShowPin] = useState<boolean>(false);
  const [settingNewPin, setSettingNewPin] = useState<boolean>(false);
  const [confirmPin, setConfirmPin] = useState<string>('');
  const [secretRecords, setSecretRecords] = useState<SecretRecord[]>([]);
  const [secretTitleInput, setSecretTitleInput] = useState<string>('');
  const [secretContentInput, setSecretContentInput] = useState<string>('');

  // Restore the Supabase auth session from SecureStore and listen for token refresh/sign-out.
  useEffect(() => {
    if (!supabaseMobile) {
      setAuthLoading(false);
      return;
    }
    supabaseMobile.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setAuthLoading(false);
    }).catch(() => setAuthLoading(false));
    const { data: { subscription } } = supabaseMobile.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });
    return () => subscription.unsubscribe();
  }, []);

  // PIN verifier and failed-attempt lockout are isolated per signed-in account.
  useEffect(() => {
    const userId = session?.user.id;
    setSecretUnlocked(false);
    setSettingNewPin(false);
    setPinInput('');
    setConfirmPin('');
    setSecretTitleInput('');
    setSecretContentInput('');
    setPinAttempts(0);
    setVaultLockoutUntil(null);
    setVaultLocked(false);
    setVaultPinSet(null);
    if (!userId) {
      setVaultPinSet(false);
      setSecretRecords([]);
      return;
    }
    let active = true;
    const lockoutKey = vaultStorageKey(VAULT_LOCKOUT_KEY, userId);
    isVaultPinSet(userId).then((configured) => {
      if (active) setVaultPinSet(configured);
    }).catch(() => {
      if (active) setVaultPinSet(false);
    });
    SecureStore.getItemAsync(lockoutKey).then((val) => {
      if (!active || !val) return;
      const until = parseInt(val, 10);
      if (!isNaN(until) && Date.now() < until) {
        setVaultLockoutUntil(until);
        setVaultLocked(true);
      } else {
        SecureStore.deleteItemAsync(lockoutKey).catch(() => {});
      }
    }).catch(() => {});
    return () => { active = false; };
  }, [session?.user.id]);

  // Load encrypted device SecureStore records only for the active account.
  useEffect(() => {
    const userId = session?.user.id;
    if (!userId || !secretUnlocked) {
      setSecretRecords([]);
      return;
    }
    let active = true;
    const loadRecords = async () => {
      const indexKey = vaultStorageKey(SECRET_RECORD_INDEX_KEY, userId);
      const rawIndex = await SecureStore.getItemAsync(indexKey);
      const parsed: unknown = rawIndex ? JSON.parse(rawIndex) : [];
      const ids = Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === 'string').slice(0, SECRET_RECORD_LIMIT) : [];
      const stored = await Promise.all(ids.map((id) => SecureStore.getItemAsync(`cognix_secret_record_v1:${userId}:${id}`)));
      const records = stored.flatMap((raw) => {
        if (!raw) return [];
        try {
          const record = JSON.parse(raw) as SecretRecord;
          return typeof record.id === 'string' && typeof record.title === 'string' && typeof record.content === 'string' ? [record] : [];
        } catch {
          return [];
        }
      });
      if (active) setSecretRecords(records);
    };
    loadRecords().catch(() => { if (active) setSecretRecords([]); });
    return () => { active = false; };
  }, [session?.user.id, secretUnlocked]);

  useEffect(() => {
    if (session?.user.id) {
      readOfflineCaptureQueue(session.user.id).then(setOfflineQueue).catch(() => setOfflineQueue([]));
    } else {
      setOfflineQueue([]);
    }
  }, [session?.user.id]);

  const loadBooks = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/brain/books`, { headers: { Authorization: `Bearer ${session?.access_token || ''}` } });
      if (res.ok) {
        const body = await res.json();
        setBooks(body.items || body || []);
      } else {
        throw new Error('Fallback to local books');
      }
    } catch {
      setBooks([]); // Do not present demo books as the user's persisted library.
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (session?.access_token) {
      loadBooks();
      loadNotes();
      loadDueCards();
    } else {
      setBooks([]);
      setNotes([]);
    }
  }, [session?.access_token]);

  const loadNotes = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/brain/notes`, {
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session?.access_token || ''}` },
      });
      if (res.ok) {
        const body = await res.json();
        setNotes(body.items || body || []);
        return;
      }
    } catch {
        // Do not display sample notes as if they belonged to the signed-in owner.
    }
    setNotes([]);
  };

  const loadDueCards = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/brain/level-up/reviews?due_only=true&limit=30`, {
        headers: { Authorization: `Bearer ${session?.access_token || ''}` },
      });
      if (!response.ok) throw new Error('Could not load scheduled flashcards.');
      const body = await response.json();
      const items = Array.isArray(body.items) ? body.items : [];
      const mapped: Flashcard[] = items.map((item: { id: string; subject: string; metadata: unknown }) => {
        const metadata = typeof item.metadata === 'string' ? JSON.parse(item.metadata) : item.metadata;
        const details = metadata && typeof metadata === 'object' ? metadata as Record<string, unknown> : {};
        return {
          id: item.id,
          question: String(details.question || ''),
          answer: String(details.answer || ''),
          source: item.subject,
          repetition: Number(details.repetition || 0),
          interval_days: Number(details.interval_days || 1),
          ease_factor: Number(details.ease_factor || 2.5),
        };
      }).filter((card: Flashcard) => card.question.length > 0 && card.answer.length > 0);
      setFlashcards(mapped);
      setCurrentCardIndex(0);
      setShowAnswer(false);
    } catch {
      setFlashcards([]);
    }
  };

  const handleGenerateFlashcards = async () => {
    const sourceNote = notes[0];
    if (!sourceNote || !session?.access_token) {
      Alert.alert('A note is required', 'Capture or save a note first, then generate flashcards from it.');
      return;
    }
    setLoading(true);
    try {
      const generatedResponse = await fetch(`${API_BASE}/api/v1/learning/quiz/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
        body: JSON.stringify({ title: sourceNote.content.slice(0, 120) || 'Brain Vault note', content: sourceNote.content, max_cards: 5 }),
      });
      if (!generatedResponse.ok) throw new Error(`Card generation failed (HTTP ${generatedResponse.status}).`);
      const generatedBody = await generatedResponse.json();
      const generatedCards = Array.isArray(generatedBody.cards) ? generatedBody.cards : [];
      let savedCount = 0;
      for (const card of generatedCards) {
        const saveResponse = await fetch(`${API_BASE}/api/v1/brain/level-up/reviews`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
          body: JSON.stringify({ subject: sourceNote.content.slice(0, 120) || 'Brain Vault note', question: card.question, answer: card.answer, source_id: sourceNote.id }),
        });
        if (!saveResponse.ok) throw new Error(`Could not persist a flashcard (HTTP ${saveResponse.status}).`);
        savedCount += 1;
      }
      await loadDueCards();
      Alert.alert('Flashcards saved', `${savedCount} card(s) were saved to your personal review schedule.`);
    } catch (error) {
      Alert.alert('Flashcard generation failed', error instanceof Error ? error.message : 'Unable to generate cards.');
    } finally {
      setLoading(false);
    }
  };

  const reviewFlashcard = async (quality: number) => {
    const card = flashcards[currentCardIndex];
    if (!card || !session?.access_token) return;
    try {
      const response = await fetch(`${API_BASE}/api/v1/brain/level-up/reviews/${encodeURIComponent(card.id)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session.access_token}` },
        body: JSON.stringify({ quality }),
      });
      if (!response.ok) throw new Error(`Review update failed (HTTP ${response.status}).`);
      setFlashcards((previous) => previous.filter((item) => item.id !== card.id));
      setCurrentCardIndex(0);
      setShowAnswer(false);
      Alert.alert('Review saved', 'Your SM-2 interval and next review date were persisted.');
    } catch (error) {
      Alert.alert('Review not saved', error instanceof Error ? error.message : 'Unable to update review schedule.');
    }
  };

  const handleSignIn = async () => {
    if (!supabaseMobile || !API_BASE) {
      Alert.alert('App configuration missing', 'Set EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY and EXPO_PUBLIC_COGNIX_API_URL in the mobile environment.');
      return;
    }
    if (!authEmail.trim() || !authPassword) {
      Alert.alert('Sign in required', 'Enter your account email and password.');
      return;
    }
    setAuthBusy(true);
    try {
      const { data, error } = await supabaseMobile.auth.signInWithPassword({
        email: authEmail.trim(),
        password: authPassword,
      });
      if (error) throw error;
      setSession(data.session);
      setAuthPassword('');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to sign in.';
      Alert.alert('Sign in failed', message);
    } finally {
      setAuthBusy(false);
    }
  };

  const handleSignOut = async () => {
    if (!supabaseMobile) return;
    const { error } = await supabaseMobile.auth.signOut();
    if (error) Alert.alert('Sign out failed', error.message);
    else setSession(null);
  };

  const handleSaveNote = async () => {
    const userId = session?.user.id;
    if (!userId || !session?.access_token || !quickInput.trim()) return;
    const newNote: CapturedNote = {
      id: Date.now().toString(),
      content: quickInput.trim(),
      tag: selectedTag,
      created_at: 'Just now'
    };
    // Optimistic UI update
    setNotes((previous) => [newNote, ...previous]);
    setQuickInput('');

    // Persist to backend. Network failures are stored on-device and can be
    // retried manually; no capture is sent to a third-party service.
    try {
      const res = await fetch(`${API_BASE}/api/v1/brain/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session?.access_token || ''}`, 'Idempotency-Key': newNote.id },
        body: JSON.stringify({ title: newNote.content.slice(0, 120) || 'Mobile capture', content: newNote.content, note_type: selectedTag, status: 'inbox' }),
      });
      if (!res.ok) {
        const queued = [...offlineQueue, { ...newNote, queued_at: new Date().toISOString() }];
        await writeOfflineCaptureQueue(userId, queued);
        setOfflineQueue(queued);
        Alert.alert('Saved Locally', 'Server rejected the capture (HTTP ' + res.status + '). It is kept on this device; authenticated API access is needed before sync.');
      } else {
        Alert.alert('Saved to Brain Vault', 'Note persisted in Brain Vault.');
      }
    } catch {
      const queued = [...offlineQueue, { ...newNote, queued_at: new Date().toISOString() }];
      await writeOfflineCaptureQueue(userId, queued);
      setOfflineQueue(queued);
      Alert.alert('Saved Locally', 'Note captured offline. Will sync when connection is restored.');
    }
  };

  const syncOfflineCaptures = async () => {
    const userId = session?.user.id;
    if (!userId || !session?.access_token || !offlineQueue.length || syncingQueue) return;
    setSyncingQueue(true);
    const remaining: QueuedCapture[] = [];
    try {
      for (const capture of offlineQueue) {
        try {
          const response = await fetch(`${API_BASE}/api/v1/brain/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${session?.access_token || ''}`, 'Idempotency-Key': capture.id },
            body: JSON.stringify({ title: capture.content.slice(0, 120) || 'Mobile capture', content: capture.content, note_type: capture.tag, status: 'inbox' }),
          });
          if (!response.ok) remaining.push(capture);
        } catch {
          remaining.push(capture);
        }
      }
      await writeOfflineCaptureQueue(userId, remaining);
      setOfflineQueue(remaining);
      Alert.alert(remaining.length ? 'Sync Paused' : 'Sync Complete', remaining.length ? `${remaining.length} capture(s) are still safely queued.` : 'All offline captures are now in your Brain Vault.');
    } finally {
      setSyncingQueue(false);
    }
  };

  const handleSaveSecretRecord = async () => {
    const userId = session?.user.id;
    const title = secretTitleInput.trim();
    const content = secretContentInput.trim();
    if (!userId || !secretUnlocked) return;
    if (!content) {
      Alert.alert('Secret content required', 'Enter the secret text you want to store.');
      return;
    }
    if (title.length > 80 || content.length > 400) {
      Alert.alert('Record too large', 'For SecureStore item limits, use a title up to 80 characters and content up to 400 characters.');
      return;
    }
    if (secretRecords.length >= SECRET_RECORD_LIMIT) {
      Alert.alert('Vault limit reached', `This device vault supports up to ${SECRET_RECORD_LIMIT} small records per account.`);
      return;
    }
    const id = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
    const record: SecretRecord = { id, title: title || 'Private item', content, created_at: new Date().toISOString() };
    const recordKey = `cognix_secret_record_v1:${userId}:${id}`;
    const indexKey = vaultStorageKey(SECRET_RECORD_INDEX_KEY, userId);
    try {
      await SecureStore.setItemAsync(recordKey, JSON.stringify(record));
      const nextIds = [...secretRecords.map((item) => item.id), id];
      await SecureStore.setItemAsync(indexKey, JSON.stringify(nextIds));
      setSecretRecords((previous) => [...previous, record]);
      setSecretTitleInput('');
      setSecretContentInput('');
      Alert.alert('Secret saved', 'The record is stored using the device SecureStore encryption and is scoped to this account.');
    } catch (error) {
      await SecureStore.deleteItemAsync(recordKey).catch(() => {});
      Alert.alert('Secret not saved', error instanceof Error ? error.message : 'SecureStore could not save this record.');
    }
  };

  const handleDeleteSecretRecord = (recordId: string) => {
    const userId = session?.user.id;
    if (!userId || !secretUnlocked) return;
    Alert.alert('Delete secret record?', 'This removes the record from this device for this account.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: async () => {
        try {
          await SecureStore.deleteItemAsync(`cognix_secret_record_v1:${userId}:${recordId}`);
          const nextRecords = secretRecords.filter((item) => item.id !== recordId);
          await SecureStore.setItemAsync(vaultStorageKey(SECRET_RECORD_INDEX_KEY, userId), JSON.stringify(nextRecords.map((item) => item.id)));
          setSecretRecords(nextRecords);
        } catch (error) {
          Alert.alert('Delete failed', error instanceof Error ? error.message : 'Could not delete the record.');
        }
      } },
    ]);
  };

  const handleSetNewPin = async () => {
    if (!/^\d{6,12}$/.test(pinInput)) {
      Alert.alert('Invalid PIN', 'PIN must contain 6 to 12 digits.');
      return;
    }
    if (!settingNewPin) {
      setSettingNewPin(true);
      setConfirmPin(pinInput);
      setPinInput('');
      return;
    }
    if (pinInput !== confirmPin) {
      Alert.alert('PIN Mismatch', 'PINs do not match. Please try again.');
      setPinInput('');
      setConfirmPin('');
      setSettingNewPin(false);
      return;
    }
    if (!session?.user.id) return;
    await setVaultPin(pinInput, session.user.id);
    setVaultPinSet(true);
    setSettingNewPin(false);
    setPinInput('');
    Alert.alert('Local PIN gate set', 'Your records use platform SecureStore encryption; the PIN is an additional local access gate.');
  };

  const handleUnlockSecret = async () => {
    const userId = session?.user.id;
    if (!userId) return;
    const lockoutKey = vaultStorageKey(VAULT_LOCKOUT_KEY, userId);
    // Check lockout
    if (vaultLockoutUntil && Date.now() < vaultLockoutUntil) {
      const remaining = Math.ceil((vaultLockoutUntil - Date.now()) / 60000);
      Alert.alert('Vault Locked', `Too many failed attempts. Try again in ${remaining} minutes.`);
      return;
    }

    if (!vaultPinSet) {
      Alert.alert('No PIN Set', 'Please set a vault PIN first.');
      return;
    }

    const isValid = await validateVaultPin(pinInput, userId);
    if (isValid) {
      setSecretUnlocked(true);
      setPinInput('');
      setPinAttempts(0);
      setVaultLocked(false);
      setVaultLockoutUntil(null);
      SecureStore.deleteItemAsync(lockoutKey).catch(() => {});
    } else {
      const newAttempts = pinAttempts + 1;
      setPinAttempts(newAttempts);
      setPinInput('');
      if (newAttempts >= VAULT_PIN_MAX_ATTEMPTS) {
        const lockoutUntil = Date.now() + VAULT_LOCKOUT_MS;
        setVaultLockoutUntil(lockoutUntil);
        setVaultLocked(true);
        // Persist lockout so it survives app restarts
        SecureStore.setItemAsync(lockoutKey, String(lockoutUntil)).catch(() => {});
        Alert.alert('Vault Locked', `Too many failed attempts. Vault locked for 15 minutes.`);
      } else {
        Alert.alert('Incorrect PIN', `Invalid PIN. ${VAULT_PIN_MAX_ATTEMPTS - newAttempts} attempts remaining.`);
      }
    }
  };

  if (authLoading) {
    return (
      <SafeAreaView style={styles.authScreen}>
        <ActivityIndicator color="#06b6d4" size="large" />
        <Text style={styles.authSubtitle}>Restoring secure Cognix session…</Text>
      </SafeAreaView>
    );
  }

  if (!session) {
    return (
      <SafeAreaView style={styles.authScreen}>
        <StatusBar style="light" />
        <Text style={styles.authTitle}>🧠 COGNIX BRAIN VAULT</Text>
        <Text style={styles.authSubtitle}>Sign in with your Cognix Supabase account to access your private notes.</Text>
        {!supabaseMobile || !API_BASE ? (
          <Text style={styles.authError}>App configuration missing. Configure the Supabase URL, publishable/anon key, and Cognix API URL in the mobile environment.</Text>
        ) : null}
        <TextInput
          style={styles.authInput}
          placeholder="Email address"
          placeholderTextColor="#64748b"
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
          value={authEmail}
          onChangeText={setAuthEmail}
        />
        <TextInput
          style={styles.authInput}
          placeholder="Password"
          placeholderTextColor="#64748b"
          secureTextEntry
          autoComplete="password"
          value={authPassword}
          onChangeText={setAuthPassword}
        />
        <TouchableOpacity style={styles.authButton} onPress={handleSignIn} disabled={authBusy || !supabaseMobile || !API_BASE}>
          <Text style={styles.authButtonText}>{authBusy ? 'Signing in…' : 'Sign in securely'}</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>🧠 COGNIX BRAIN VAULT</Text>
          <Text style={styles.headerSubtitle}>Personal Knowledge OS & Second Brain</Text>
        </View>
        <TouchableOpacity style={styles.badgeBtn} onPress={loadBooks}>
          <Text style={styles.badgeBtnText}>⚡ {books.length} Books</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.badgeBtn} onPress={handleSignOut} accessibilityRole="button" accessibilityLabel="Sign out">
          <Text style={styles.badgeBtnText}>Sign out</Text>
        </TouchableOpacity>
      </View>

      {/* Navigation Tabs */}
      <View style={styles.tabsRow}>
        <TouchableOpacity
          style={[styles.tabItem, activeTab === 'capture' && styles.activeTabItem]}
          onPress={() => setActiveTab('capture')}
        >
          <Text style={[styles.tabText, activeTab === 'capture' && styles.activeTabText]}>
            ⚡ Quick Capture
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === 'vault' && styles.activeTabItem]}
          onPress={() => setActiveTab('vault')}
        >
          <Text style={[styles.tabText, activeTab === 'vault' && styles.activeTabText]}>
            📚 Vault
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === 'learn' && styles.activeTabItem]}
          onPress={() => setActiveTab('learn')}
        >
          <Text style={[styles.tabText, activeTab === 'learn' && styles.activeTabText]}>
            🎯 Learn ({flashcards.length} due)
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tabItem, activeTab === 'secret' && styles.activeTabItem]}
          onPress={() => setActiveTab('secret')}
        >
          <Text style={[styles.tabText, activeTab === 'secret' && styles.activeTabText]}>
            🔒 Secret
          </Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      <View style={styles.body}>
        {/* TAB 1: QUICK CAPTURE */}
        {activeTab === 'capture' && (
          <ScrollView contentContainerStyle={{ padding: 16 }}>
            <View style={styles.card}>
              <Text style={styles.cardTitle}>⚡ Capture a Thought or Research Note</Text>
              {offlineQueue.length > 0 && (
                <TouchableOpacity style={styles.queueBanner} onPress={syncOfflineCaptures} disabled={syncingQueue} accessibilityRole="button" accessibilityLabel="Sync offline captures">
                  <Text style={styles.queueBannerText}>{syncingQueue ? 'Syncing local captures…' : `${offlineQueue.length} offline capture${offlineQueue.length === 1 ? '' : 's'} · Tap to sync`}</Text>
                </TouchableOpacity>
              )}
              <TextInput
                style={styles.textInput}
                placeholder="What's on your mind? Note, quote, link or insight..."
                placeholderTextColor="#64748b"
                multiline
                numberOfLines={3}
                value={quickInput}
                onChangeText={setQuickInput}
              />

              {/* Tag Selector */}
              <View style={styles.tagsRow}>
                {['#idea', '#research', '#todo', '#quote', '#myanmar'].map((tag) => (
                  <TouchableOpacity
                    key={tag}
                    style={[styles.tagPill, selectedTag === tag && styles.activeTagPill]}
                    onPress={() => setSelectedTag(tag)}
                  >
                    <Text style={[styles.tagPillText, selectedTag === tag && styles.activeTagPillText]}>
                      {tag}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity style={styles.saveBtn} onPress={handleSaveNote}>
                <Text style={styles.saveBtnText}>Save into Brain Vault →</Text>
              </TouchableOpacity>
            </View>

            {/* Recent Notes Stream */}
            <Text style={styles.sectionHeader}>Recent Captures ({notes.length})</Text>
            {notes.map((n) => (
              <View key={n.id} style={styles.noteItem}>
                <View style={styles.noteHeader}>
                  <Text style={styles.noteTag}>{n.tag}</Text>
                  <Text style={styles.noteTime}>{n.created_at}</Text>
                </View>
                <Text style={styles.noteContent}>{n.content}</Text>
              </View>
            ))}
          </ScrollView>
        )}

        {/* TAB 2: KNOWLEDGE VAULT */}
        {activeTab === 'vault' && (
          <FlatList
            data={books}
            keyExtractor={(item) => item.id}
            contentContainerStyle={{ padding: 16 }}
            renderItem={({ item }) => (
              <View style={styles.bookCard}>
                <View style={styles.bookHeader}>
                  <Text style={styles.bookCategory}>{item.category || 'General Knowledge'}</Text>
                  <Text style={styles.chunkBadge}>{item.chunk_count} Chunks</Text>
                </View>
                <Text style={styles.bookTitle}>{item.title}</Text>
                <Text style={styles.bookAuthor}>{item.author || 'Author'}</Text>
                <View style={styles.bookFooter}>
                  <Text style={styles.aiBadge}>✨ AI Distillation Ready</Text>
                  <TouchableOpacity
                    style={styles.readBtn}
                    onPress={() => Alert.alert(item.title, `Synthesizing ${item.chunk_count} chunks with pgvector RAG.`)}
                  >
                    <Text style={styles.readBtnText}>AI Review →</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          />
        )}

        {/* TAB 3: OWNER-SCOPED PERSISTED SPACED REPETITION */}
        {activeTab === 'learn' && (
          <View style={styles.learnContainer}>
            <Text style={styles.learnTitle}>🎯 Personal Spaced Repetition</Text>
            {flashcards.length === 0 ? (
              <View style={styles.flashcardBox}>
                <Text style={styles.cardQuestion}>No flashcards are due right now.</Text>
                <Text style={styles.cardAnswer}>Generate cards from one of your saved Brain Vault notes to create a personal, persisted review schedule.</Text>
                {notes.length > 0 ? (
                  <TouchableOpacity style={styles.revealBtn} onPress={handleGenerateFlashcards} disabled={loading}>
                    <Text style={styles.revealBtnText}>{loading ? 'Generating and saving…' : 'Generate from latest note'}</Text>
                  </TouchableOpacity>
                ) : (
                  <Text style={styles.learnSubtitle}>Save a note first in Quick Capture.</Text>
                )}
              </View>
            ) : (
              <>
                <Text style={styles.learnSubtitle}>
                  Card {currentCardIndex + 1} of {flashcards.length} • {flashcards[currentCardIndex].source}
                </Text>
                <View style={styles.flashcardBox}>
                  <Text style={styles.cardQuestion}>{flashcards[currentCardIndex].question}</Text>
                  {showAnswer ? (
                    <View style={styles.answerBox}>
                      <Text style={styles.answerLabel}>Answer:</Text>
                      <Text style={styles.cardAnswer}>{flashcards[currentCardIndex].answer}</Text>
                    </View>
                  ) : (
                    <TouchableOpacity style={styles.revealBtn} onPress={() => setShowAnswer(true)}>
                      <Text style={styles.revealBtnText}>🔍 Reveal Answer</Text>
                    </TouchableOpacity>
                  )}
                </View>
                <View style={styles.flashcardActions}>
                  <TouchableOpacity style={styles.reviewAgainBtn} onPress={() => reviewFlashcard(2)} disabled={!showAnswer}>
                    <Text style={styles.actionBtnText}>Again (1 day)</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.gotItBtn} onPress={() => reviewFlashcard(4)} disabled={!showAnswer}>
                    <Text style={styles.actionBtnText}>Good (SM-2)</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>
        )}

        {/* TAB 4: SECRET VAULT */}
        {activeTab === 'secret' && (
          <View style={styles.secretContainer}>
            {!secretUnlocked ? (
              <View style={styles.pinBox}>
                <Text style={styles.lockIcon}>🔐</Text>
                <Text style={styles.secretHeading}>
                  {vaultPinSet ? 'Local PIN Lock' : (settingNewPin ? 'Confirm Vault PIN' : 'Set Vault PIN')}
                </Text>
                <Text style={styles.secretSubheading}>
                  {vaultPinSet
                    ? 'The PIN is a local access gate. Saved records use platform SecureStore encryption.'
                    : (settingNewPin
                      ? 'Re-enter the PIN to confirm this account-local access gate.'
                      : 'Create a PIN with 6 to 12 digits for this account-local access gate.')}
                </Text>

                <TextInput
                  style={styles.pinInput}
                  placeholder={vaultPinSet ? 'PIN' : (settingNewPin ? 'Confirm PIN' : 'New PIN')}
                  placeholderTextColor="#64748b"
                  keyboardType="numeric"
                  secureTextEntry={!showPin}
                  maxLength={12}
                  value={pinInput}
                  onChangeText={setPinInput}
                />

                <TouchableOpacity
                  style={styles.unlockBtn}
                  onPress={vaultPinSet ? handleUnlockSecret : handleSetNewPin}
                  disabled={vaultPinSet === null}
                >
                  <Text style={styles.unlockBtnText}>
                    {vaultPinSet ? 'Unlock Vault 🔓' : (settingNewPin ? 'Confirm PIN 🔐' : 'Set PIN 🔐')}
                  </Text>
                </TouchableOpacity>
              </View>
            ) : (
              <ScrollView contentContainerStyle={{ padding: 16 }}>
                <View style={styles.secretHeaderRow}>
                  <Text style={styles.unlockedHeading}>🔓 Local PIN Gate</Text>
                  <TouchableOpacity
                    style={styles.lockNowBtn}
                    onPress={() => { setSecretUnlocked(false); setSecretTitleInput(''); setSecretContentInput(''); }}
                  >
                    <Text style={styles.lockNowText}>Lock 🔒</Text>
                  </TouchableOpacity>
                </View>

                <View style={styles.secretNoteCard}>
                  <Text style={styles.secretFormTitle}>Add a private record</Text>
                  <TextInput
                    style={styles.secretFormInput}
                    placeholder="Title (optional)"
                    placeholderTextColor="#64748b"
                    value={secretTitleInput}
                    onChangeText={setSecretTitleInput}
                    maxLength={80}
                  />
                  <TextInput
                    style={[styles.secretFormInput, styles.secretContentInput]}
                    placeholder="Secret content (up to 400 characters)"
                    placeholderTextColor="#64748b"
                    value={secretContentInput}
                    onChangeText={setSecretContentInput}
                    maxLength={400}
                    multiline
                  />
                  <TouchableOpacity style={styles.secretSaveBtn} onPress={handleSaveSecretRecord}>
                    <Text style={styles.secretSaveBtnText}>Save securely</Text>
                  </TouchableOpacity>
                  <Text style={styles.secretStorageCaption}>Stored locally in OS SecureStore, scoped to this account. This is not synced to the backend.</Text>
                </View>
                {secretRecords.length === 0 ? (
                  <Text style={styles.secretNoteText}>No private records saved yet.</Text>
                ) : secretRecords.map((record) => (
                  <View key={record.id} style={styles.secretNoteCard}>
                    <View style={styles.secretRecordHeader}>
                      <Text style={styles.secretRecordTitle}>{record.title}</Text>
                      <TouchableOpacity onPress={() => handleDeleteSecretRecord(record.id)}>
                        <Text style={styles.secretDeleteText}>Delete</Text>
                      </TouchableOpacity>
                    </View>
                    <Text style={styles.secretNoteText}>{record.content}</Text>
                    <Text style={styles.secretStorageCaption}>{new Date(record.created_at).toLocaleDateString()}</Text>
                  </View>
                ))}
              </ScrollView>
            )}
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#090d16' },
  authScreen: { flex: 1, backgroundColor: '#090d16', justifyContent: 'center', alignItems: 'center', padding: 24 },
  authTitle: { color: '#06b6d4', fontSize: 21, fontWeight: 'bold', marginBottom: 10, textAlign: 'center' },
  authSubtitle: { color: '#94a3b8', fontSize: 13, textAlign: 'center', marginBottom: 24, maxWidth: 320 },
  authError: { color: '#fbbf24', fontSize: 12, textAlign: 'center', marginBottom: 16, maxWidth: 320 },
  authInput: { backgroundColor: '#0f172a', borderRadius: 8, color: '#f8fafc', padding: 13, borderWidth: 1, borderColor: '#1e293b', width: '100%', maxWidth: 360, marginBottom: 12 },
  authButton: { backgroundColor: '#06b6d4', paddingVertical: 13, paddingHorizontal: 24, borderRadius: 8, width: '100%', maxWidth: 360, alignItems: 'center', marginTop: 8 },
  authButtonText: { color: '#090d16', fontWeight: 'bold', fontSize: 14 },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  headerTitle: { color: '#06b6d4', fontSize: 18, fontWeight: 'bold', letterSpacing: 0.5 },
  headerSubtitle: { color: '#94a3b8', fontSize: 11, marginTop: 2 },
  badgeBtn: { backgroundColor: '#164e63', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12 },
  badgeBtnText: { color: '#22d3ee', fontSize: 11, fontWeight: 'bold' },
  queueBanner: { backgroundColor: '#3f2a0b', borderWidth: 1, borderColor: '#a16207', borderRadius: 8, padding: 9, marginBottom: 12 },
  queueBannerText: { color: '#fde68a', fontSize: 12, fontWeight: '600' },
  tabsRow: {
    flexDirection: 'row',
    backgroundColor: '#0f172a',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b'
  },
  tabItem: { flex: 1, paddingVertical: 12, alignItems: 'center' },
  activeTabItem: { borderBottomWidth: 2, borderBottomColor: '#06b6d4' },
  tabText: { color: '#64748b', fontSize: 11, fontWeight: '600' },
  activeTabText: { color: '#06b6d4' },
  body: { flex: 1 },
  card: {
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1e293b',
    marginBottom: 16
  },
  cardTitle: { color: '#f8fafc', fontSize: 15, fontWeight: 'bold', marginBottom: 12 },
  textInput: {
    backgroundColor: '#090d16',
    borderRadius: 8,
    color: '#f8fafc',
    padding: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
    textAlignVertical: 'top'
  },
  tagsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 12 },
  tagPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: '#1e293b'
  },
  activeTagPill: { backgroundColor: '#0891b2' },
  tagPillText: { color: '#94a3b8', fontSize: 11 },
  activeTagPillText: { color: '#ffffff', fontWeight: 'bold' },
  saveBtn: {
    backgroundColor: '#06b6d4',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 14
  },
  saveBtnText: { color: '#090d16', fontWeight: 'bold', fontSize: 13 },
  sectionHeader: { color: '#94a3b8', fontSize: 13, fontWeight: 'bold', marginBottom: 8 },
  noteItem: {
    backgroundColor: '#0f172a',
    padding: 14,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#1e293b'
  },
  noteHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  noteTag: { color: '#06b6d4', fontSize: 11, fontWeight: 'bold' },
  noteTime: { color: '#64748b', fontSize: 11 },
  noteContent: { color: '#f1f5f9', fontSize: 13, lineHeight: 18 },
  bookCard: {
    backgroundColor: '#0f172a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#1e293b'
  },
  bookHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  bookCategory: { color: '#06b6d4', fontSize: 11, fontWeight: 'bold' },
  chunkBadge: { color: '#94a3b8', fontSize: 11 },
  bookTitle: { color: '#f8fafc', fontSize: 16, fontWeight: 'bold', marginTop: 6 },
  bookAuthor: { color: '#64748b', fontSize: 12, marginTop: 2 },
  bookFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#1e293b',
    paddingTop: 8
  },
  aiBadge: { color: '#38bdf8', fontSize: 11 },
  readBtn: { backgroundColor: '#1e293b', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 6 },
  readBtnText: { color: '#06b6d4', fontSize: 11, fontWeight: 'bold' },
  learnContainer: { flex: 1, padding: 20, alignItems: 'center', justifyContent: 'center' },
  learnTitle: { color: '#f8fafc', fontSize: 17, fontWeight: 'bold', marginBottom: 4 },
  learnSubtitle: { color: '#94a3b8', fontSize: 12, marginBottom: 20 },
  flashcardBox: {
    width: '100%',
    minHeight: 220,
    backgroundColor: '#0f172a',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#06b6d4',
    padding: 20,
    justifyContent: 'center',
    alignItems: 'center'
  },
  cardQuestion: { color: '#f8fafc', fontSize: 16, fontWeight: 'bold', textAlign: 'center', lineHeight: 24 },
  answerBox: { marginTop: 16, paddingTop: 16, borderTopWidth: 1, borderTopColor: '#1e293b', width: '100%' },
  answerLabel: { color: '#06b6d4', fontSize: 11, fontWeight: 'bold', marginBottom: 4 },
  cardAnswer: { color: '#cbd5e1', fontSize: 14, lineHeight: 20 },
  revealBtn: { marginTop: 20, backgroundColor: '#0891b2', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8 },
  revealBtnText: { color: '#ffffff', fontWeight: 'bold', fontSize: 13 },
  flashcardActions: { flexDirection: 'row', gap: 16, marginTop: 24 },
  reviewAgainBtn: { backgroundColor: '#334155', paddingVertical: 12, paddingHorizontal: 20, borderRadius: 8 },
  gotItBtn: { backgroundColor: '#10b981', paddingVertical: 12, paddingHorizontal: 24, borderRadius: 8 },
  actionBtnText: { color: '#ffffff', fontWeight: 'bold', fontSize: 13 },
  secretContainer: { flex: 1 },
  pinBox: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  lockIcon: { fontSize: 48, marginBottom: 16 },
  secretHeading: { color: '#f8fafc', fontSize: 18, fontWeight: 'bold', marginBottom: 8 },
  secretSubheading: { color: '#94a3b8', fontSize: 12, textAlign: 'center', marginBottom: 24, paddingHorizontal: 20 },
  pinInput: {
    backgroundColor: '#0f172a',
    borderRadius: 8,
    color: '#f8fafc',
    padding: 12,
    borderWidth: 1,
    borderColor: '#06b6d4',
    width: 160,
    textAlign: 'center',
    fontSize: 20,
    letterSpacing: 8
  },
  unlockBtn: { backgroundColor: '#06b6d4', paddingHorizontal: 24, paddingVertical: 12, borderRadius: 8, marginTop: 16 },
  unlockBtnText: { color: '#090d16', fontWeight: 'bold', fontSize: 14 },
  secretHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  unlockedHeading: { color: '#10b981', fontSize: 16, fontWeight: 'bold' },
  lockNowBtn: { backgroundColor: '#334155', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 6 },
  lockNowText: { color: '#cbd5e1', fontSize: 11 },
  secretNoteCard: {
    backgroundColor: '#0f172a',
    padding: 16,
    borderRadius: 8,
    marginBottom: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#06b6d4'
  },
  secretNoteText: { color: '#f1f5f9', fontSize: 14 },
  secretFormTitle: { color: '#f8fafc', fontSize: 14, fontWeight: 'bold', marginBottom: 10 },
  secretFormInput: { backgroundColor: '#090d16', color: '#f8fafc', borderColor: '#334155', borderWidth: 1, borderRadius: 8, padding: 10, marginBottom: 10 },
  secretContentInput: { minHeight: 90, textAlignVertical: 'top' },
  secretSaveBtn: { backgroundColor: '#06b6d4', borderRadius: 8, paddingVertical: 10, alignItems: 'center' },
  secretSaveBtnText: { color: '#090d16', fontWeight: 'bold' },
  secretStorageCaption: { color: '#64748b', fontSize: 10, marginTop: 8 },
  secretRecordHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  secretRecordTitle: { color: '#06b6d4', fontSize: 14, fontWeight: 'bold', flex: 1 },
  secretDeleteText: { color: '#f87171', fontSize: 12, fontWeight: 'bold', paddingLeft: 12 }
});

export default AppWithBoundary;
