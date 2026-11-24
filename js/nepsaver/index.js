// nepsaver - adds the latest unplayed episode of every podcast you follow on Spotify
// to a playlist of your choice.
const axios = require('axios')
const querystring = require('querystring')
const path = require('path')
const express = require('express')
const cors = require('cors')
require('dotenv').config()

const PORT = process.env.PORT || 5000
const CLIENT_ID = process.env.CLIENT_ID
const CLIENT_SECRET = process.env.CLIENT_SECRET
const REDIRECT_URL = process.env.REDIRECT_URL || `http://localhost:${PORT}/callback`
let PLAYLIST_ID = process.env.PLAYLIST_ID

const AUTH_URL = 'https://accounts.spotify.com/authorize'
const TOKEN_URL = 'https://accounts.spotify.com/api/token'
const API_BASE_URL = 'https://api.spotify.com/v1/'

// episodes listened to for more than this are considered "already played"
const PLAYED_THRESHOLD_MS = 30000

if (!CLIENT_ID || !CLIENT_SECRET) {
  console.error('CLIENT_ID and CLIENT_SECRET are required (see .env.example)')
  process.exit(1)
}

// single-user, in-memory session: the token obtained after the Spotify login
const session = {}

async function api(method, url, data) {
  const opts = {
    method,
    url: url.startsWith('http') ? url : API_BASE_URL + url,
    headers: { Authorization: 'Bearer ' + session.access_token }
  }
  if (data) {
    opts.data = data
    opts.headers['Content-Type'] = 'application/json'
  }
  const response = await axios(opts)
  return response.data
}

const getSavedShows = () => api('get', 'me/shows?limit=50')
const getLatestEpisode = (showId) => api('get', `shows/${showId}/episodes?limit=1&offset=0`)
const addToPlaylist = (playlistId, uris) => api('post', `playlists/${playlistId}/tracks`, { uris })

const app = express()
app.use(express.json())
app.use(express.urlencoded({ extended: true }))
app.use(cors())

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'web', 'index.html'))
})

app.post('/submit', (req, res) => {
  const id = req.body.playlist_id
  if (id && id.length > 18) PLAYLIST_ID = id
  res.redirect('/login')
})

app.get('/login', (req, res) => {
  const params = {
    response_type: 'code',
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URL,
    scope: 'user-read-private user-library-read user-read-playback-position ' +
      'playlist-modify-public playlist-modify-private',
    show_dialog: true
  }
  res.redirect(AUTH_URL + '?' + querystring.stringify(params))
})

app.get('/callback', async (req, res) => {
  if (!req.query.code) return res.redirect('/login')
  try {
    const response = await axios.post(TOKEN_URL, querystring.stringify({
      grant_type: 'authorization_code',
      code: req.query.code,
      redirect_uri: REDIRECT_URL,
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET
    }))
    session.access_token = response.data.access_token
    session.refresh_token = response.data.refresh_token
    session.expires_at = Math.floor(Date.now() / 1000) + response.data.expires_in
    res.redirect('/podcast')
  } catch (e) {
    console.error('Token exchange failed:', e.message)
    res.redirect('/login')
  }
})

app.get('/podcast', async (req, res) => {
  if (!session.access_token || Date.now() / 1000 > session.expires_at) return res.redirect('/login')
  if (!PLAYLIST_ID) return res.status(400).send('No playlist ID: set PLAYLIST_ID or enter it on the home page.')
  try {
    const shows = (await getSavedShows()).items
    const toSave = []
    for (const { show } of shows) {
      for (const episode of (await getLatestEpisode(show.id)).items) {
        const rp = episode.resume_point
        const played = rp.fully_played || rp.resume_position_ms > PLAYED_THRESHOLD_MS
        console.log(`${played ? 'played ' : 'NEW    '} ${show.name} - ${episode.name}`)
        if (!played) toSave.push(episode)
      }
    }
    if (toSave.length) await addToPlaylist(PLAYLIST_ID, toSave.map((e) => e.uri))
    res.type('text/plain').send(
      `${toSave.length} episode(s) added to the playlist:\n` + toSave.map((e) => '- ' + e.name).join('\n'))
  } catch (e) {
    console.error('Spotify API error:', e.response?.status, e.message)
    res.status(502).send('Spotify API error: ' + e.message)
  }
})

app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`))
