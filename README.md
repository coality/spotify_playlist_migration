# Spotify Playlist Migrator

Application TUI pour migrer vos playlists Spotify d'un ancien compte vers un nouveau, sans Premium requis.

## Objectif

Ce projet permet de copier vos playlists Spotify entre deux comptes en utilisant une interface TUI (Terminal User Interface) simple et intuitive. Aucune connaissance technique n'est requise - tout se fait depuis le terminal.

## Fonctionnalités

- **Interface TUI moderne** : Navigation simple au clavier
- **Authentification OAuth2** : kopie de l'URL, collage du callback
- **Migration flexible** : Une playlist ou toutes les playlists
- **Mode Dry Run** : Tester sans effectuer de modifications
- **Progression en temps réel** : Voyez l'avancement de la migration
- **Gestion d'erreurs** : Reprise propre sur erreur, logs lisibles
- **Mode headless** : Fonctionne en SSH sans serveur X

## Prérequis

- Python 3.12+
- Deux comptes Spotify (source et target)
- Accès à [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)

## Installation

```bash
# Cloner ou créer le répertoire
cd spotify_playlist_migration

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\Activate.ps1  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer le package en mode développement
pip install -e .
```

## Configuration

### Via la TUI

Lancez l'application et sélectionnez "Configuration" dans le menu pour saisir vos identifiants Spotify Developer.

```bash
spotify-migrator
```

La configuration est stockée dans `~/.spotify_migrator/store/config.json`.

## Configuration Spotify Developer

### 1. Créer les applications Spotify

1. Allez sur [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Cliquez sur "Create App"
3. Remplissez le nom et la description
4. Pour `Redirect URI`, entrez `http://localhost:8080`
5. **Créez DEUX applications** : une pour le compte source, une pour le target
6. Notez les `Client ID` et `Client Secret` pour chaque

## Lancement

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'application TUI
spotify-migrator
```

## Utilisation de la TUI

### Écran principal

L'écran d'accueil affiche:
- État de connexion source (✓ ou ✗)
- État de connexion target (✓ ou ✗)
- Menu principal

### Menu principal

| Option | Description |
|--------|-------------|
| Configuration | Configurer les identifiants Spotify |
| Authentifier compte SOURCE | Authentifier le compte source |
| Authentifier compte TARGET | Authentifier le compte target |
| Lister les playlists source | Voir les playlists du compte source |
| Migrer une playlist | Migrer une playlist sélectionnée |
| Migrer toutes les playlists | Migrer toutes les playlists |
| Voir les logs | Afficher les logs de l'application |
| Quitter | Fermer l'application |

### Procédure d'authentification

1. Sélectionnez "Authentifier compte SOURCE" (ou TARGET)
2. L'application génère une URL d'autorisation
3. **Copiez l'URL** affichée dans la console
4. Ouvrez l'URL dans votre navigateur
5. Autorisez l'application Spotify
6. **Copiez l'URL de redirection** (ou juste le code)
7. **Collez-la** dans le champ de saisie de la TUI
8. Appuyez sur "Valider"

### Migration de playlists

1. Authentifiez-vous sur source ET target
2. Sélectionnez "Migrer une playlist" ou "Migrer toutes les playlists"
3. Choisissez le mode:
   - **Migrer** : Effectue la migration réelle
   - **Dry Run** : Simule sans modifier
4. Suivez la progression en temps réel

## Commandes clavier

| Touche | Action |
|--------|--------|
| `↑` / `↓` | Navigation dans les listes |
| `Enter` | Sélectionner |
| `←` / `Esc` | Retour / Annuler |
| `Ctrl+C` | Coller depuis le presse-papier |

## Tests

```bash
# Lancer tous les tests
pytest -v

# Avec couverture
pytest --cov=spotify_migrator --cov-report=term-missing

# Tests spécifiques
pytest tests/test_models/ -v
pytest tests/test_services/ -v
```

## Structure du projet

```
spotify_playlist_migration/
├── src/spotify_migrator/
│   ├── __init__.py
│   ├── __main__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── track.py
│   │   ├── playlist.py
│   │   └── migration.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── exceptions.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── exceptions.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── migrator.py
│   │   └── pagination.py
│   ├── store/
│   │   ├── __init__.py
│   │   ├── token_store.py
│   │   └── config_store.py
│   └── tui/
│       ├── __init__.py
│       ├── app.py
│       ├── screens/
│       │   ├── __init__.py
│       │   ├── home.py
│       │   ├── auth.py
│       │   ├── playlists.py
│       │   ├── migrate.py
│       │   ├── logs.py
│       │   └── setup.py
│       └── widgets/
│           ├── __init__.py
│           ├── status.py
│           ├── playlist_list.py
│           └── progress.py
├── tests/
│   ├── __init__.py
│   └── conftest.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Limitations connues

### Limites de l'API Spotify

1. **Rate Limiting** : L'API limite les requêtes. Retry automatique implémenté.
2. **Playlists collaboratives** : Non copiables (propriété du créateur)
3. **Pistes locales** : Non copiables (n'existent pas sur Spotify)
4. **Informations non copiées** : Date de création, followers, position

### Limites de l'application

- Nécessite connexion internet stable
- Ne supporte pas la migration incrémentale

## Considérations de sécurité

- Configuration et tokens stockés dans `~/.spotify_migrator/` avec permissions 0o600
- HTTPS recommandé pour les URIs de redirection

## Dépannage

### "Non connecté au compte source"
→ Authentifiez-vous d'abord avec "Authentifier compte SOURCE"

### "Token expiré"
→ Ré-authentifiez le compte concerné

### "Rate limited"
→ Attendez quelques minutes et réessayez

### Erreur 404 sur playlist
→ La playlist peut avoir été supprimée ou être privée

## Licence

MIT
