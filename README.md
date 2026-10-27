# 棒球 The Real

A 3D baseball batting and pitching game that runs in the browser (three.js r128).

## Play

Open `baseball.html` in Chrome. It needs internet the first time to load three.js from the CDN.

You manage the **Hawks** against the CPU **Comets** in a nine-inning game. A coin toss decides who bats first; three outs switch sides. You bat when the Hawks are up and pitch when they're in the field. Fielding and baserunning are automatic, including double plays.

- **Batting:** move the mouse to aim the bat, left-click to swing, right-click for the bunt stance, and hold A or D to aim the bunt.
- **Pitching:** press 1–5 to pick one of your pitcher's pitches, aim with the mouse, then hold the left button for power and release to throw. The red zone grows as he tires; reaching it throws a mistake. **B** opens the bullpen to change pitchers.
- **N** toggles sound. On phones and tablets, use the on-screen buttons and drag to aim.

Every player has ratings. Batters: contact (timing window and CPU contact rate), power (exit speed and lift), speed (running and range in the field) and eye (CPU chase rate). Pitchers: top velocity, control, stamina (pitches before tiring), stuff (break) and their own pitch mix. Starters go long, closers throw hardest. The CPU manager relieves tired pitchers and brings in its closer for a save.

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
