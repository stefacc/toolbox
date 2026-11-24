# nepsaver - new podcast episodes to a Spotify playlist

Spotify has no "queue of new episodes" for the podcasts you follow. nepsaver looks at
every show you follow, takes the **latest episode** of each one and, if you haven't
played it yet, **adds it to a playlist** of your choice. Then you just play that playlist.

An episode counts as already played if it is marked as fully played or you listened
to more than 30 seconds of it.

## Setup

1. Create an app on the [Spotify developer dashboard](https://developer.spotify.com/dashboard)
   and add `http://localhost:5000/callback` as **Redirect URI**.
2. Create (or pick) a playlist and copy its ID: the part after `/playlist/` in the share link.
3. Configure and start:

```
npm install
cp .env.example .env      # fill in CLIENT_ID, CLIENT_SECRET, PLAYLIST_ID
npm start
```

4. Open http://localhost:5000, optionally paste another playlist ID, and click
   **Login with Spotify**. After the login the episodes are added and the page lists them.

Run it again whenever you want to refresh the playlist (e.g. once a day).

## Notes

- Single user, local use: the Spotify token is only kept in memory.
- Only the first 50 followed shows are checked.
- Requested scopes: read your library and playback position, modify your playlists.
- `.env` contains your app secret: it is git-ignored, keep it that way.
