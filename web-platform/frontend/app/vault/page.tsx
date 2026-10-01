'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { listVaultItems, saveVaultItem, ApiVaultItem } from '@/lib/api';

function bytesToBase64(bytes: Uint8Array) { let binary=''; bytes.forEach(b=>binary+=String.fromCharCode(b)); return btoa(binary); }
function base64ToBytes(value:string) { const binary=atob(value); return Uint8Array.from(binary,c=>c.charCodeAt(0)); }
async function deriveKey(password:string,salt:Uint8Array) { const material=await crypto.subtle.importKey('raw',new TextEncoder().encode(password),'PBKDF2',false,['deriveKey']); return crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:600000,hash:'SHA-256'},material,{name:'AES-GCM',length:256},false,['encrypt','decrypt']); }
async function encryptSecret(password:string,plain:string) { const salt=crypto.getRandomValues(new Uint8Array(16)); const nonce=crypto.getRandomValues(new Uint8Array(12)); const key=await deriveKey(password,salt); const cipher=await crypto.subtle.encrypt({name:'AES-GCM',iv:nonce},key,new TextEncoder().encode(plain)); return {ciphertext:bytesToBase64(new Uint8Array(cipher)),nonce:bytesToBase64(nonce),kdf_salt:bytesToBase64(salt),kdf_params:{algorithm:'PBKDF2-SHA256',iterations:600000,key_length:256}}; }
async function decryptSecret(item:ApiVaultItem,password:string) { const params=item.kdf_params; const material=await crypto.subtle.importKey('raw',new TextEncoder().encode(password),'PBKDF2',false,['deriveKey']); const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:base64ToBytes(item.kdf_salt),iterations:Number(params.iterations||600000),hash:'SHA-256'},material,{name:'AES-GCM',length:256},false,['decrypt']); const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:base64ToBytes(item.nonce)},key,base64ToBytes((item as ApiVaultItem & {ciphertext?:string}).ciphertext||'')); return new TextDecoder().decode(plain); }

export default function VaultPage() {
  const [items,setItems]=useState<ApiVaultItem[]>([]); const [label,setLabel]=useState(''); const [secret,setSecret]=useState(''); const [password,setPassword]=useState(''); const [revealed,setRevealed]=useState(''); const [error,setError]=useState('');
  const load=async()=>setItems((await listVaultItems()).items); useEffect(()=>{load().catch(()=>setError('Vault requires a persistent database.'));},[]);
  const save=async()=>{if(!label||!secret||!password)return;setError('');try{await saveVaultItem({label,...await encryptSecret(password,secret)});setSecret('');await load();}catch(e){setError(e instanceof Error?e.message:'Unable to save secret');}};
  return <AppShell><PageHeader title="Secret Vault" description="The server stores ciphertext only; plaintext stays in this browser." />
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]"><SectionCard title="Encrypt and save"><div className="space-y-3">
      <input value={label} onChange={e=>setLabel(e.target.value)} placeholder="Label" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <input value={password} onChange={e=>setPassword(e.target.value)} type="password" placeholder="Vault password" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <textarea value={secret} onChange={e=>setSecret(e.target.value)} rows={7} placeholder="Secret text" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <button onClick={save} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Encrypt</button></div></SectionCard>
      <SectionCard title="Vault items" description={items.length+' encrypted records'}><div className="space-y-3">{items.map(item=><article key={item.id} className="rounded-lg border border-border/60 p-4"><div className="font-medium">{item.label}</div><button onClick={()=>{const p=window.prompt('Vault password');if(p)decryptSecret(item,p).then(setRevealed).catch(()=>setError('Wrong password or corrupted ciphertext.'));}} className="mt-3 rounded-md border border-border px-3 py-1.5 text-xs">Decrypt locally</button></article>)}</div>
      {revealed&&<pre className="mt-4 whitespace-pre-wrap rounded-lg border border-border/60 p-4 text-sm">{revealed}</pre>}{error&&<p className="mt-3 text-sm text-destructive">{error}</p>}</SectionCard></div></AppShell>;
}
