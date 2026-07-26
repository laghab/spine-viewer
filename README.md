# Spine Viewer 🦴

A drag-and-drop viewer for [Spine](http://esotericsoftware.com/) skeletons. Drop a `.zip` or a folder
containing your exported `.json` + `.atlas` + texture files, and instantly preview every skeleton in a
grid — click one to zoom into a full animated view with bones, slots, skins, and an animation picker.

Built for quickly sanity-checking exported Spine assets (from an artist, a build pipeline, or your own
project) without opening the Spine editor or wiring them into a game engine first.

**Live demo:** https://spine-viewer-rho.vercel.app

## Running it

No build step — it's a single `index.html`.

- **Standalone:** just open `index.html` in a browser (or deploy it as-is, e.g. to Vercel). Everything is
  parsed and rendered client-side; nothing is uploaded anywhere.
- **With persistence:** run `python3 server.py` and open `http://localhost:8080` for a small local server
  that stores what you drop in `uploads/`, so it's still there next time you reload.
