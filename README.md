# 棒球 The Real

A 3D baseball batting and pitching game that runs in the browser (three.js r128).

## Play

Open `baseball.html` in Chrome. It needs internet the first time to load three.js from the CDN.

- **M** switches between batting and pitching mode.
- **Batting:** move the mouse to aim the bat, left-click to swing, right-click for the bunt stance, and hold A or D to aim the bunt.
- **Pitching:** press 1–5 to pick a pitch, aim with the mouse, then hold the left button for power and release to throw. If the meter reaches the red zone, the pitch is a mistake. **R** rests the pitcher.

## Layout

| Path | What it is |
| --- | --- |
| `baseball.html` | The whole game |
| `mocap/clips.js` | Pitch, swing, bunt and run motion, generated from `mocap/raw/` |
| `mocap/raw/` | CMU motion-capture source files (subjects 124 and 9) |
| `tools/amc2json.py` | Converts the CMU files into `mocap/clips.js` |
| `models/male.js` | Player body, embedded so the game works from `file://` |
| `models/raw/` | Original model download |

Regenerate the motion clips:

```bash
python3 -I tools/amc2json.py mocap/raw mocap/clips.js
```

## Credits

- Motion: [CMU Graphics Lab Motion Capture Database](http://mocap.cs.cmu.edu/), subject 124 (pitch, swing, bunt) and subject 9 (run). Free to use; the data may not be resold.
- Player body: "3D Male Base Mesh" by orange-juice-games ([GitHub re-upload](https://github.com/BoQsc/Godot-3D-Male-Base-Mesh)), CC0.
