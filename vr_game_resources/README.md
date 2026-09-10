# Game-cache overlay

Only files maintained by HL2Q3VR belong under `srceng/`. The cache builder merges them after
copying a user's legal Half-Life 2 installation. Paths must match the final headset layout.

Current runtime overlay:

- `hl2/cfg/sourcevr_hl2.cfg` — synchronous material queue and VR defaults;
- `hl2/materials/vgui/inworldui*.vmt` — materials for menu and intro render targets;
- `hl2/models/questvr/` — compiled controller models;
- `hl2/materials/models/questvr/` — controller materials and VTF textures.
- `hl2/models/hl2questvr/` and `hl2/materials/models/player/` — tracked hand model and skin;
- `hl2/models/weapons/vr_*` and `hl2/materials/models/weapons/vr_*/` — PCVR-derived tracked
  weapon models, animated parts, left-handed variants and materials used by milestone 0.75;
- `hl2/materials/effects/hl2quest_rpg_laser.vmt` and `hl2/materials/sprites/vr_physcannon_*`
  — Quest-compatible weapon effects;
- `hl2/custom/hl2quest_pcvr_menu/` — menu fonts and loose GameUI resources.
- `questvr/shaders/fxc/` — the engine-compatible Portal shader cache; both cache builders
  verify all 366 files and the hashes of the two shader families responsible for white materials.

`supportsvr 1` is patched into the copied `hl2/gameinfo.txt` by the builder so the user's
current file is preserved. Never place Valve VPKs, maps, voice files or saves here. Before a
public release, verify redistribution permission for every PCVR-derived binary asset listed
above; this repository is currently a local reference snapshot.
