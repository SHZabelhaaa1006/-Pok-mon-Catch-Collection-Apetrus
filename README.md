# PokéCatch

Plataforma de coleção de Pokémon com API Django/DRF, PostgreSQL, Firebase Auth e frontend Vue 3/Vite.

## Rodando localmente

### Backend

1. Crie o banco PostgreSQL `pokemon_db`.
2. `cd backend && python3.13 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. Copie `.env.example` para `.env` e preencha a senha do PostgreSQL.
5. Baixe o JSON da conta de serviço no Firebase Console e salve como `backend/firebase_service_account.json`. O arquivo é ignorado pelo Git.
6. `python manage.py makemigrations collection && python manage.py migrate`
7. Para promover um usuário autenticado a administrador, altere `Profile.is_admin` para `true` no Django Admin.
8. `python manage.py runserver`

### Frontend

1. `cd frontend && npm install`
2. Copie `.env.example` para `.env` e preencha as credenciais Web do Firebase.
3. `npm run dev`

## Regras implementadas

- A rodada de captura é persistida por usuário e expira após 30 minutos, sem Celery ou Redis.
- O endpoint de disponibilidade recalcula a rodada quando chamado após a expiração; o frontend atualiza o contador a cada segundo e consulta novamente ao zerar.
- Cada captura aceita de 1 a 5 IDs da rodada atual e impede ultrapassar 20 Pokémon na Pokédex.
- CRUD `/api/pokemons/` exige usuário autenticado com `Profile.is_admin=true`.
- `/api/catch/available/`, `/api/catch/claim/`, `/api/my-pokedex/` e a remoção da Pokédex exigem token Firebase Bearer.

## Segurança

O JSON de service account contém uma chave privada e não deve ser commitado. Foi incluído apenas um modelo em `backend/firebase_service_account.json.example`. As credenciais fornecidas no enunciado também devem ser revogadas/rotacionadas no Firebase Console.