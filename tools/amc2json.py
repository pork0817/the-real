"""Convert CMU ASF/AMC mocap into compact joint-position clips for baseball.html.

Usage: python3 -I tools/amc2json.py mocap/raw mocap/clips.js
Output is a JS file defining window.MOCAP = {clip: {fps, n, joints:[...], f:[flat xyz...], ...}}
in the game's character frame (metres, y up, ground at 0).
"""
import json, math, sys, os

def euler(ax, ay, az):  # Rz(az) @ Ry(ay) @ Rx(ax), degrees
    ax, ay, az = map(math.radians, (ax, ay, az))
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    Ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    Rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return mm(mm(Rz, Ry), Rx)

def mm(A, B): return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mv(A, v): return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]
def tr(A): return [list(r) for r in zip(*A)]
def add(a, b, s=1.0): return [a[i] + s * b[i] for i in range(3)]

def parse_asf(path):
    bones, hier, root_order = {}, {}, None
    lines = [l.strip() for l in open(path)]
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith(':root'):
            i += 1
            while not lines[i].startswith(':'):
                if lines[i].startswith('order'): root_order = lines[i].split()[1:]
                i += 1
            continue
        if l == 'begin':
            b = {'dof': []}
            i += 1
            while lines[i] != 'end':
                t = lines[i].split()
                if t[0] == 'name': b['name'] = t[1]
                elif t[0] == 'direction': b['dir'] = list(map(float, t[1:4]))
                elif t[0] == 'length': b['len'] = float(t[1])
                elif t[0] == 'axis': b['axis'] = list(map(float, t[1:4]))
                elif t[0] == 'dof': b['dof'] = t[1:]
                i += 1
            b['C'] = euler(*b['axis']); b['Ci'] = tr(b['C'])
            bones[b['name']] = b
        if l.startswith(':hierarchy'):
            i += 2
            while lines[i] != 'end':
                t = lines[i].split(); hier[t[0]] = t[1:]; i += 1
        i += 1
    return bones, hier, root_order

def parse_amc(path):
    frames, cur = [], None
    for l in open(path):
        l = l.strip()
        if not l or l[0] in '#:': continue
        if l.isdigit():
            cur = {}; frames.append(cur); continue
        t = l.split(); cur[t[0]] = list(map(float, t[1:]))
    return frames

def fk(bones, hier, fr):
    pos, mat = {}, {}
    r = fr['root']
    pos['root'] = list(r[:3]); mat['root'] = euler(*r[3:6])
    stack = ['root']
    while stack:
        p = stack.pop()
        for c in hier.get(p, []):
            b = bones[c]; vals = fr.get(c, [])
            ang = {'rx': 0, 'ry': 0, 'rz': 0}
            for k, d in enumerate(b['dof']): ang[d] = vals[k]
            M = mm(mm(mm(mat[p], b['C']), euler(ang['rx'], ang['ry'], ang['rz'])), b['Ci'])
            mat[c] = M; pos[c] = add(pos[p], mv(M, b['dir']), b['len'])
            stack.append(c)
    return pos, mat

# game joint <- CMU bone end
MAP = {'pelv': 'root', 'lHip': 'lhipjoint', 'rHip': 'rhipjoint', 'lKn': 'lfemur', 'rKn': 'rfemur', 'lFt': 'ltibia', 'rFt': 'rtibia',
       'lToe': 'lfoot', 'rToe': 'rfoot', 'chest': 'upperback', 'neck': 'thorax', 'lSh': 'lclavicle', 'rSh': 'rclavicle',
       'lEl': 'lhumerus', 'rEl': 'rhumerus', 'lHa': 'lwrist', 'rHa': 'rwrist'}
JOINTS = list(MAP) + ['head']

def clip_positions(bones, hier, frames):
    out, hands = [], []
    for fr in frames:
        pos, mat = fk(bones, hier, fr)
        d = {j: pos[b] for j, b in MAP.items()}
        d['head'] = [(pos['upperneck'][i] + pos['head'][i]) / 2 for i in range(3)]
        out.append(d); hands.append((mat['lhand'], mat['rhand']))
    return out, hands

def load(raw, name, bones, hier):
    fr = parse_amc(os.path.join(raw, name))
    return clip_positions(bones, hier, fr)

def nrm(v):
    l = math.sqrt(sum(x * x for x in v)) or 1e-9
    return [x / l for x in v]

def speeds(P, j):
    return [math.dist(P[i + 1][j], P[i][j]) * 120 for i in range(len(P) - 1)]

def bat_axis(P, H, a, b):
    """constant axis in the bottom (left) hand's frame that best matches the wrist-to-wrist direction"""
    acc = [0, 0, 0]
    for i in range(a, b):
        d = A_(P[i]['rHa'], P[i]['lHa'])
        if math.sqrt(sum(x * x for x in d)) < 1.5: continue
        acc = add(acc, mv(tr(H[i][0]), nrm(d)))
    return nrm(acc)

def A_(p, q): return [p[k] - q[k] for k in range(3)]

def process(kind, P, H, bones):
    s = 0.895 / (bones['lfemur']['len'] + bones['ltibia']['len'])
    n = len(P); vr, vl = speeds(P, 'rHa'), speeds(P, 'lHa')
    ev = {}
    if kind == 'pitch':
        rel = vr.index(max(vr)); a = max(0, rel - 216); b = min(n - 1, rel + 108)
        dirv = A_(P[rel + 1]['rHa'], P[rel - 1]['rHa']); target = (0, 1); origin = P[a]['rFt']
        ev['release'] = (rel - a) / 120
    else:
        both = [x + y for x, y in zip(vr, vl)]; pk = both.index(max(both))
        a = max(0, pk - (150 if kind == 'swing' else 220)); b = min(n - 1, pk + 130)
        dirv = A_(P[a]['lFt'], P[a]['rFt']); target = (1, 0)
        origin = [(P[a]['lFt'][k] + P[a]['rFt'][k]) / 2 for k in range(3)]
        ev['peak'] = (pk - a) / 120
    th = math.atan2(target[0], target[1]) - math.atan2(dirv[0], dirv[2])
    c, sn = math.cos(th), math.sin(th)
    rot = lambda v: [v[0] * c + v[2] * sn, v[1], -v[0] * sn + v[2] * c]
    gmin = min(min(P[i]['lFt'][1], P[i]['rFt'][1]) for i in range(a, b + 1))
    def T(p):
        q = rot([p[0] - origin[0], 0, p[2] - origin[2]])
        return [q[0] * s, (p[1] - gmin) * s + .05, q[2] * s]
    frames = [{j: T(P[i][j]) for j in JOINTS} for i in range(a, b + 1)]
    bat = None
    if kind != 'pitch':
        ax = bat_axis(P, H, a, b + 1)
        bat = [rot(mv(H[i][0], ax)) for i in range(a, b + 1)]
    # foot locking: pin planted feet so they don't slide
    for fj, tj in (('lFt', 'lToe'), ('rFt', 'rToe')):
        anchor = None
        for i in range(len(frames)):
            f = frames[i]; prev = frames[max(0, i - 1)][fj]
            v = math.dist([f[fj][0], f[fj][2]], [prev[0], prev[2]]) * 120
            if f[fj][1] < .09 and v < .5:
                if anchor is None: anchor = (f[fj][0], f[fj][2], f[tj][0] - f[fj][0], f[tj][2] - f[fj][2])
                f[fj][0], f[fj][2] = anchor[0], anchor[1]; f[tj][0], f[tj][2] = anchor[0] + anchor[2], anchor[1] + anchor[3]
            else: anchor = None
    if kind == 'bunt':  # frame where the bat is squared and pushed furthest toward the pitcher
        pk = int(ev['peak'] * 120); rng = range(pk, min(len(frames), pk + 120))
        ev['hold'] = max(rng, key=lambda i: frames[i]['lHa'][0] + frames[i]['rHa'][0]) / 120
    step = 2
    idx = list(range(0, len(frames), step))
    out = {'dt': step / 120, 'n': len(idx), 'J': JOINTS, 'ev': ev,
           'f': [round(x, 3) for i in idx for j in JOINTS for x in frames[i][j]]}
    if bat: out['bat'] = [round(x, 3) for i in idx for x in bat[i]]
    return out

def main(raw, outp):
    bones, hier, _ = parse_asf(os.path.join(raw, '124.asf'))
    res = {}
    for key, fn in [('pitch', '124_01.amc'), ('swing', '124_07.amc'), ('bunt', '124_08.amc')]:
        P, H = load(raw, fn, bones, hier)
        res[key] = process(key, P, H, bones)
        print(key, res[key]['n'], 'frames', res[key]['ev'])
    with open(outp, 'w') as f:
        f.write('// Generated by tools/amc2json.py from the CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), subject 124.\n')
        f.write('window.MOCAP=' + json.dumps(res, separators=(',', ':')) + ';\n')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
