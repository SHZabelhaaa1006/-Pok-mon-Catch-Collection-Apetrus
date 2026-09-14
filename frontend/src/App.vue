<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onAuthStateChanged, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth'
import { auth } from './firebase'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const user = ref(null)
const authMode = ref('login')
const email = ref('')
const password = ref('')
const busy = ref(false)
const error = ref('')
const notice = ref('')
const tab = ref('hunt')
const available = ref([])
const pokedex = ref([])
const selected = ref([])
const seconds = ref(0)
const adminPokemon = ref([])
const form = ref({ name: '', pokedex_number: '', type: '', description: '', image: null })
let timer

const isAdmin = computed(() => user.value?.admin === true)
const formattedTime = computed(() => `${String(Math.floor(seconds.value / 60)).padStart(2, '0')}:${String(seconds.value % 60).padStart(2, '0')}`)

async function token() { return user.value?.getIdToken() }
async function api(path, options = {}) {
  const headers = { ...(options.headers || {}), Authorization: `Bearer ${await token()}` }
  const response = await fetch(`${API}${path}`, { ...options, headers })
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || 'Não foi possível concluir a operação.') }
  return response.status === 204 ? null : response.json()
}
async function authenticate() {
  busy.value = true; error.value = ''
  try {
    const result = authMode.value === 'login'
      ? await signInWithEmailAndPassword(auth, email.value, password.value)
      : await createUserWithEmailAndPassword(auth, email.value, password.value)
    user.value = result.user
  } catch (err) { error.value = err.message } finally { busy.value = false }
}
async function loadData() {
  if (!user.value) return
  try { const [round, mine, profile] = await Promise.all([api('/catch/available/'), api('/my-pokedex/'), api('/me/')]); available.value = round.pokemons; seconds.value = round.seconds_remaining; pokedex.value = mine.pokemons; user.value.admin = profile.is_admin }
  catch (err) { error.value = err.message }
}
async function loadAdmin() { try { adminPokemon.value = await api('/pokemons/') } catch (err) { error.value = err.message } }
async function claim() {
  if (!selected.value.length) return
  try { await api('/catch/claim/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pokemon_ids: selected.value }) }); notice.value = 'Capturas adicionadas à sua Pokédex.'; selected.value = []; await loadData() }
  catch (err) { error.value = err.message }
}
async function release(pokemonId) { try { await api(`/my-pokedex/${pokemonId}/`, { method: 'DELETE' }); pokedex.value = pokedex.value.filter(item => item.pokemon.id !== pokemonId) } catch (err) { error.value = err.message } }
function choose(id) { selected.value = selected.value.includes(id) ? selected.value.filter(item => item !== id) : [...selected.value, id] }
function imageFor(pokemon) { return pokemon.image_url || 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png' }
function fileChanged(event) { form.value.image = event.target.files[0] }
async function savePokemon() {
  const data = new FormData(); Object.entries(form.value).forEach(([key, value]) => { if (value !== '' && value !== null) data.append(key, value) })
  try { await api('/pokemons/', { method: 'POST', body: data }); notice.value = 'Pokémon cadastrado.'; form.value = { name: '', pokedex_number: '', type: '', description: '', image: null }; await loadAdmin() } catch (err) { error.value = err.message }
}
async function removePokemon(id) { try { await api(`/pokemons/${id}/`, { method: 'DELETE' }); adminPokemon.value = adminPokemon.value.filter(item => item.id !== id) } catch (err) { error.value = err.message } }
function logout() { signOut(auth); user.value = null }

onMounted(() => { onAuthStateChanged(auth, async current => { user.value = current; if (current) { const result = await current.getIdTokenResult(); current.admin = result.claims.admin === true; await loadData() } }); timer = setInterval(async () => { if (seconds.value > 0) seconds.value--; else await loadData() }, 1000) })
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <main class="shell">
    <section v-if="!user" class="auth-card">
      <div class="brand-mark">PK</div><p class="eyebrow">PokéCatch / coleção viva</p>
      <h1>Monte uma Pokédex<br /><em>que é só sua.</em></h1>
      <p class="muted">Capture os encontros disponíveis antes que a próxima rodada chegue.</p>
      <form @submit.prevent="authenticate"><label>E-mail<input v-model="email" type="email" required /></label><label>Senha<input v-model="password" type="password" minlength="6" required /></label><button class="primary" :disabled="busy">{{ busy ? 'Entrando...' : authMode === 'login' ? 'Entrar na expedição' : 'Criar conta' }}</button></form>
      <button class="link-button" @click="authMode = authMode === 'login' ? 'register' : 'login'">{{ authMode === 'login' ? 'Ainda não tenho conta' : 'Já tenho uma conta' }}</button><p v-if="error" class="error">{{ error }}</p>
    </section>

    <template v-else>
      <header class="topbar"><div><span class="brand-mark small">PK</span><span class="wordmark">PokéCatch</span></div><div class="profile"><span>{{ email || user.email }}</span><button class="icon-button" title="Sair" @click="logout">↗</button></div></header>
      <section class="intro"><div><p class="eyebrow">Olá, treinador</p><h1>Seu próximo encontro<br /><em>está esperando.</em></h1></div><div class="capacity"><span>POKÉDEX</span><strong>{{ pokedex.length }}<small>/20</small></strong><div class="meter"><i :style="{ width: `${pokedex.length * 5}%` }"></i></div></div></section>
      <nav class="tabs"><button :class="{ active: tab === 'hunt' }" @click="tab = 'hunt'">Encontros <span>{{ available.length }}</span></button><button :class="{ active: tab === 'dex' }" @click="tab = 'dex'">Minha Pokédex <span>{{ pokedex.length }}</span></button><button v-if="isAdmin" :class="{ active: tab === 'admin' }" @click="tab = 'admin'; loadAdmin()">Administração</button></nav>
      <p v-if="error" class="toast error">{{ error }} <button @click="error = ''">×</button></p><p v-if="notice" class="toast">{{ notice }} <button @click="notice = ''">×</button></p>

      <section v-if="tab === 'hunt'" class="content"><div class="section-heading"><div><p class="eyebrow">Rodada atual</p><h2>Encontros selvagens</h2></div><div class="countdown"><span>próxima rotação</span><strong>{{ formattedTime }}</strong></div></div><p class="hint">Escolha até cinco Pokémon para adicionar à sua coleção.</p><div class="pokemon-grid"><button v-for="pokemon in available" :key="pokemon.id" class="pokemon-card" :class="{ selected: selected.includes(pokemon.id) }" @click="choose(pokemon.id)"><span class="select-dot">{{ selected.includes(pokemon.id) ? '✓' : '' }}</span><img :src="imageFor(pokemon)" :alt="pokemon.name" /><span class="number">Nº {{ String(pokemon.pokedex_number).padStart(3, '0') }}</span><h3>{{ pokemon.name }}</h3><span class="type">{{ pokemon.type }}</span></button></div><button class="primary claim" :disabled="!selected.length" @click="claim">Capturar {{ selected.length ? `· ${selected.length}` : '' }}</button></section>

      <section v-if="tab === 'dex'" class="content"><div class="section-heading"><div><p class="eyebrow">Sua coleção</p><h2>Minha Pokédex</h2></div><div class="big-count">{{ pokedex.length }}<small>/20 capturados</small></div></div><div v-if="!pokedex.length" class="empty">Sua Pokédex ainda está vazia.<br />Volte aos encontros para começar.</div><div class="pokemon-grid"><article v-for="capture in pokedex" :key="capture.id" class="pokemon-card owned"><img :src="imageFor(capture.pokemon)" :alt="capture.pokemon.name" /><span class="number">Nº {{ String(capture.pokemon.pokedex_number).padStart(3, '0') }}</span><h3>{{ capture.pokemon.name }}</h3><span class="type">{{ capture.pokemon.type }}</span><button class="release" @click="release(capture.pokemon.id)">Libertar</button></article></div></section>

      <section v-if="tab === 'admin' && isAdmin" class="content admin"><div class="section-heading"><div><p class="eyebrow">Controle do mundo</p><h2>Gerenciar Pokémon</h2></div></div><form class="admin-form" @submit.prevent="savePokemon"><input v-model="form.name" placeholder="Nome" required /><input v-model="form.pokedex_number" type="number" placeholder="Nº Pokédex" required /><input v-model="form.type" placeholder="Tipo" required /><input v-model="form.description" placeholder="Descrição" /><input type="file" accept="image/*" @change="fileChanged" /><button class="primary">Cadastrar</button></form><div class="admin-list"><div v-for="pokemon in adminPokemon" :key="pokemon.id"><span>#{{ pokemon.pokedex_number }} · {{ pokemon.name }}</span><button class="release" @click="removePokemon(pokemon.id)">Excluir</button></div></div></section>
    </template>
  </main>
</template>
