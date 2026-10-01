import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { Button, FlatList, SafeAreaView, Text, View } from 'react-native';

const API = process.env.EXPO_PUBLIC_COGNIX_API_URL || 'http://localhost:8000';
export default function App() {
  const [books,setBooks]=useState<{id:string;title:string;chunk_count:number}[]>([]); const [error,setError]=useState('');
  const load=async()=>{try{const response=await fetch(API+'/brain/books');if(!response.ok)throw new Error('API request failed');const body=await response.json();setBooks(body.items||[]);}catch(e){setError(e instanceof Error?e.message:'Unable to connect');}};
  useEffect(()=>{load();},[]);
  return <SafeAreaView style={{flex:1,padding:24}}><StatusBar style="auto"/><Text style={{fontSize:28,fontWeight:'700'}}>Cognix Brain Vault</Text><Text style={{marginTop:8,marginBottom:16}}>Mobile reader foundation</Text><Button title="Refresh library" onPress={load}/>{error?<Text style={{marginTop:16}}>{error}</Text>:null}<FlatList style={{marginTop:16}} data={books} keyExtractor={item=>item.id} renderItem={({item})=><View style={{paddingVertical:12,borderBottomWidth:1,borderBottomColor:'#ddd'}}><Text style={{fontWeight:'600'}}>{item.title}</Text><Text>{item.chunk_count} chunks</Text></View>}/></SafeAreaView>;
}
