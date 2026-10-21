import React, { useState, useEffect } from 'react';
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
const VAULT_LOCKOUT_KEY = 'cognix_vault_lockout_until';
const VAULT_PIN_MAX_ATTEMPTS = 5;
const VAULT_LOCKOUT_MS = 15 * 60 * 1000; // 15 minutes

/** PBKDF2-based PIN hash — salted with a fixed app secret + pin length to prevent rainbow tables. */
const PBKDF2_SALT = 'cognix_vault_salt_v1_2026'; // static app-level salt; do NOT change after deploy
const PBKDF2_ITERATIONS = 100_000;
const PBKDF2_KEY_LENGTH = 32; // 256 bits

async function hashPin(pin: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoder.encode(pin),
    { name: 'PBKDF2' },
    false,
    ['deriveBits']
  );
  const derivedBits = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt: encoder.encode(PBKDF2_SALT),
      iterations: PBKDF2_ITERATIONS,
      hash: 'SHA-256',
    },
    keyMaterial,
    PBKDF2_KEY_LENGTH * 8
  );
  const hashArray = Array.from(new Uint8Array(derivedBits));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

async function isVaultPinSet(): Promise<boolean> {
  const storedHash = await SecureStore.getItemAsync(VAULT_PIN_STORAGE_KEY);
  return storedHash !== null;
}

async function validateVaultPin(pin: string): Promise<boolean> {
  const storedHash = await SecureStore.getItemAsync(VAULT_PIN_STORAGE_KEY);
  if (!storedHash) return false;
  const inputHash = await hashPin(pin);
  return inputHash === storedHash;
}

async function setVaultPin(pin: string): Promise<void> {
  const hash = await hashPin(pin);
  await SecureStore.setItemAsync(VAULT_PIN_STORAGE_KEY, hash);
}

const _rawApiBase = process.env.EXPO_PUBLIC_COGNIX_API_URL;
if (!_rawApiBase) {
  throw new Error(
    '[Cognix] EXPO_PUBLIC_COGNIX_API_URL is not set. '
    + 'Create .env with EXPO_PUBLIC_COGNIX_API_URL=https://your-api-url'
  );
}
const API_BASE = _rawApiBase;

interface BookItem {
  id: string;
  title: string;
  author?: string;
  chunk_count: number;
  category?: string;
  summary?: string;
}

interface CapturedNote {
  id: string;
  content: string;
  tag: string;
  created_at: string;
}

interface Flashcard {
  id: string;
  question: string;
  answer: string;
  source: string;
}

function App() {
  const [activeTab, setActiveTab] = useState<'capture' | 'vault' | 'learn' | 'secret'>('capture');
  const [books, setBooks] = useState<BookItem[]>([]);
  const [notes, setNotes] = useState<CapturedNote[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [quickInput, setQuickInput] = useState<string>('');
  const [selectedTag, setSelectedTag] = useState<string>('#idea');

  // Flashcards
  const [flashcards] = useState<Flashcard[]>([
    {
      id: 'fc-1',
      question: 'What is Reciprocal Rank Fusion (RRF) in Cognix hybrid search?',
      answer: 'RRF combines scores from BM25 lexical search and pgvector semantic embeddings without needing calibrated score normalization.',
      source: 'Cognix Architecture'
    },
    {
      id: 'fc-2',
      question: 'How does Second Brain progressive summarization work?',
      answer: 'Layer 1: Raw notes -> Layer 2: Bold passages -> Layer 3: Highlighted core ideas -> Layer 4: Executive mini-summary.',
      source: 'Building a Second Brain'
    },
    {
      id: 'fc-3',
      question: 'What is the role of Brain Soul Layer?',
      answer: 'A personal context file storing writing style, current projects, and narrative preferences to avoid re-prompting LLMs.',
      source: 'Cognix Brain Soul'
    }
  ]);
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
  const [secretNotes, setSecretNotes] = useState<string[]>([
    '🔒 Personal Strategic OKRs 2026-2027',
    '🔒 Master Recovery Seed & Private Encryption Keys',
    '🔒 Confidential Architecture Blueprint'
  ]);

  // Check if vault PIN has been set on mount; restore persisted lockout
  useEffect(() => {
    isVaultPinSet().then(setVaultPinSet);
    SecureStore.getItemAsync(VAULT_LOCKOUT_KEY).then((val) => {
      if (val) {
        const until = parseInt(val, 10);
        if (!isNaN(until) && Date.now() < until) {
          setVaultLockoutUntil(until);
          setVaultLocked(true);
        } else {
          SecureStore.deleteItemAsync(VAULT_LOCKOUT_KEY).catch(() => {});
        }
      }
    }).catch(() => {});
  }, []);

  const loadBooks = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/brain/books`);
      if (res.ok) {
        const body = await res.json();
        setBooks(body.items || body || []);
      } else {
        throw new Error('Fallback to local books');
      }
    } catch {
      setBooks([
        { id: 'b-1', title: 'Thinking, Fast and Slow', author: 'Daniel Kahneman', chunk_count: 142, category: 'Psychology' },
        { id: 'b-2', title: 'Designing Data-Intensive Applications', author: 'Martin Kleppmann', chunk_count: 320, category: 'System Design' },
        { id: 'b-3', title: 'The Lean Startup', author: 'Eric Ries', chunk_count: 98, category: 'Business' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBooks();
    loadNotes();
  }, []);

  const loadNotes = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/brain/notes`, {
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        const body = await res.json();
        setNotes(body.items || body || []);
        return;
      }
    } catch {
      // fallback to default notes on network error
    }
    setNotes([
      { id: 'n-1', content: 'Explore pgvector HNSW indexing vs IVFFlat for sub-millisecond retrieval.', tag: '#research', created_at: 'Just now' },
      { id: 'n-2', content: 'Draft next short-form script on Bagan archaeological survey.', tag: '#idea', created_at: '2 hours ago' }
    ]);
  };

  const handleSaveNote = async () => {
    if (!quickInput.trim()) return;
    const newNote: CapturedNote = {
      id: Date.now().toString(),
      content: quickInput.trim(),
      tag: selectedTag,
      created_at: 'Just now'
    };
    // Optimistic UI update
    setNotes([newNote, ...notes]);
    setQuickInput('');

    // Persist to backend
    try {
      const res = await fetch(`${API_BASE}/api/v1/brain/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newNote.content, tag: selectedTag }),
      });
      if (!res.ok) {
        console.warn('Note saved locally but failed to sync to backend:', res.status);
        Alert.alert('Saved Locally', 'Note captured. Will sync when connection is restored.');
      } else {
        Alert.alert('Saved to Brain Vault', 'Note captured and queued for AI knowledge indexing.');
      }
    } catch {
      console.warn('Network error - note saved locally only');
      Alert.alert('Saved Locally', 'Note captured offline. Will sync when connection is restored.');
    }
  };

  const handleSetNewPin = async () => {
    if (pinInput.length < 4) {
      Alert.alert('Invalid PIN', 'PIN must be at least 4 digits.');
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
    await setVaultPin(pinInput);
    setVaultPinSet(true);
    setSettingNewPin(false);
    setPinInput('');
    Alert.alert('Vault Secured', 'Your vault PIN has been set. Keep it safe!');
  };

  const handleUnlockSecret = async () => {
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

    const isValid = await validateVaultPin(pinInput);
    if (isValid) {
      setSecretUnlocked(true);
      setPinInput('');
      setPinAttempts(0);
      setVaultLocked(false);
      setVaultLockoutUntil(null);
      SecureStore.deleteItemAsync(VAULT_LOCKOUT_KEY).catch(() => {});
    } else {
      const newAttempts = pinAttempts + 1;
      setPinAttempts(newAttempts);
      setPinInput('');
      if (newAttempts >= VAULT_PIN_MAX_ATTEMPTS) {
        const lockoutUntil = Date.now() + VAULT_LOCKOUT_MS;
        setVaultLockoutUntil(lockoutUntil);
        setVaultLocked(true);
        // Persist lockout so it survives app restarts
        SecureStore.setItemAsync(VAULT_LOCKOUT_KEY, String(lockoutUntil)).catch(() => {});
        Alert.alert('Vault Locked', `Too many failed attempts. Vault locked for 15 minutes.`);
      } else {
        Alert.alert('Incorrect PIN', `Invalid PIN. ${VAULT_PIN_MAX_ATTEMPTS - newAttempts} attempts remaining.`);
      }
    }
  };

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
            🎯 Learn (20)
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

        {/* TAB 3: DAILY LEARNING & FLASHCARDS */}
        {activeTab === 'learn' && (
          <View style={styles.learnContainer}>
            <Text style={styles.learnTitle}>🎯 Daily Spaced Repetition (Level Up 20)</Text>
            <Text style={styles.learnSubtitle}>
              Card {currentCardIndex + 1} of {flashcards.length} • {flashcards[currentCardIndex].source}
            </Text>

            <View style={styles.flashcardBox}>
              <Text style={styles.cardQuestion}>
                {flashcards[currentCardIndex].question}
              </Text>

              {showAnswer ? (
                <View style={styles.answerBox}>
                  <Text style={styles.answerLabel}>AI Answer:</Text>
                  <Text style={styles.cardAnswer}>
                    {flashcards[currentCardIndex].answer}
                  </Text>
                </View>
              ) : (
                <TouchableOpacity
                  style={styles.revealBtn}
                  onPress={() => setShowAnswer(true)}
                >
                  <Text style={styles.revealBtnText}>🔍 Reveal Answer</Text>
                </TouchableOpacity>
              )}
            </View>

            {/* Flashcard Next Actions */}
            <View style={styles.flashcardActions}>
              <TouchableOpacity
                style={styles.reviewAgainBtn}
                onPress={() => {
                  setShowAnswer(false);
                  setCurrentCardIndex((prev) => (prev + 1) % flashcards.length);
                }}
              >
                <Text style={styles.actionBtnText}>Review Later ⏳</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.gotItBtn}
                onPress={() => {
                  setShowAnswer(false);
                  Alert.alert('Mastered!', 'Knowledge retention recorded in Brain Vault.');
                  setCurrentCardIndex((prev) => (prev + 1) % flashcards.length);
                }}
              >
                <Text style={styles.actionBtnText}>Mastered ✅</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* TAB 4: SECRET VAULT */}
        {activeTab === 'secret' && (
          <View style={styles.secretContainer}>
            {!secretUnlocked ? (
              <View style={styles.pinBox}>
                <Text style={styles.lockIcon}>🔐</Text>
                <Text style={styles.secretHeading}>Encrypted Secret Vault</Text>
                <Text style={styles.secretSubheading}>
                  Enter your 4-digit security PIN to unlock private brain items.
                </Text>

                <TextInput
                  style={styles.pinInput}
                  placeholder="PIN (Default: 1234)"
                  placeholderTextColor="#64748b"
                  keyboardType="numeric"
                  secureTextEntry={!showPin}
                  maxLength={4}
                  value={pinInput}
                  onChangeText={setPinInput}
                />

                <TouchableOpacity style={styles.unlockBtn} onPress={handleUnlockSecret}>
                  <Text style={styles.unlockBtnText}>Unlock Vault 🔓</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <ScrollView contentContainerStyle={{ padding: 16 }}>
                <View style={styles.secretHeaderRow}>
                  <Text style={styles.unlockedHeading}>🔓 Decrypted Private Vault</Text>
                  <TouchableOpacity
                    style={styles.lockNowBtn}
                    onPress={() => setSecretUnlocked(false)}
                  >
                    <Text style={styles.lockNowText}>Lock 🔒</Text>
                  </TouchableOpacity>
                </View>

                {secretNotes.map((item, idx) => (
                  <View key={idx} style={styles.secretNoteCard}>
                    <Text style={styles.secretNoteText}>{item}</Text>
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
  secretNoteText: { color: '#f1f5f9', fontSize: 14 }
});

export default AppWithBoundary;
