#!/bin/env python

from datetime import datetime, timedelta
from itertools import product
import random
import json
import re

#=-
# Utils

def cont(p):
    """
    cont(p)

    Check if `p` can be queried for containment.
    """
    try:
        0 in p
    except TypeError:
        return False
    return True

#=-
# Numbers / Intervals / PitchClasses

class Integral:
    """
    Integral(n)

    Type of integers.
    """
    def __init__(self, n):
        self.n = self.norm(int(n))

    @classmethod
    def norm(cls, n):
        """
        norm(cls, n)

        Normalize the internal representation of `n` according to numerical
        type `cls`.
        """
        # In the case of simple integers, no normalization is required.
        return n

    def __add__(self, s):
        return self.__class__(self.n + int(s))
    def __sub__(self, s):
        return self.__class__(self.n - int(s))
    def __mul__(self, s):
        return self.__class__(self.n * int(s))
    def __radd__(self, s):
        return self.__add__(s)
    def __rsub__(self, s):
        return self.__sub__(s)
    def __rmul__(self, s):
        return self.__mul__(s)
    def __neg__(self):
        return self.__class__(-self.n)
    def __iadd__(self, s):
        self.n+= int(s)
        self.n = self.norm(self.n)
    def __isub__(self, s):
        self.n-= int(s)
        self.n = self.norm(self.n)
    def __imul__(self, s):
        self.n*= int(s)
        self.n = self.norm(self.n)
    def __eq__(self, s):
        try:
            return self.n == int(s)
        except:
            return False

    def __str__(self):
        return str(self.n)
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.n)
    def __int__(self):
        return self.n
    def __hash__(self):
        return self.__int__()
    @property
    def value(self):
        return self.n

class Z12(Integral):
    @classmethod
    def norm(cls, n):
        # Internal representation as a residue mod 12.
        return n % 12

def memoize(function):
    """
    memoize(function)

    Implements a value cache for function `function`.

    If the wrapper is applied to argument `x` for the first time, `function(x)`
    is stored in an internal cache of the wrapper and is subsequently returned.
    On future runs, if the argument matches `x`, the stored value is returned
    without passing `x` to `function` a second time.
    """
    memo = {}
    def wrapper(cls):
        if cls.__name__ in memo:
            return memo[cls.__name__]
        else:
            rv = function(cls)
            memo[cls.__name__] = rv
            return rv
    return wrapper

@memoize
def Torsor(cls):
    """
    Torsor(cls)
    
    A parametric class. Implements a set of labels equipped with a free and
    transitive action of a group `cls`. This means that the only operations
    available are the addition and subtraction of x∊`cls` from a given element
    of a torsor.

    By default, the labels correspond to elements of the group. To attach
    custom labels, implement a subclass of Torsor.
    """
    class t:
        def __init__(self, *q, **k):
            self.v = cls(*q,**k)

        def __add__(self, s):
            return self.__class__(self.v + s)
        def __sub__(self, s):
            return self.__class__(self.v - s)
        def __iadd__(self, s):
            self.v+= s
        def __isub__(self, s):
            self.v-= s
        def __eq__(self, s):
            return self.v == s if isinstance(s,t) else False
        @property
        def value(self):
            return self.v.value
        def __int__(self):
            return self.v.value
        def __hash__(self):
            return self.__int__()

    t.__name__ = "Torsor({})".format(cls.__name__)
    return t

# Semitone -> interval class.
INTERVAL_NUMBER = {
    0: 1,
    1: 2,
    2: 2,
    3: 3,
    4: 3,
    5: 4,
    6: 5,
    7: 5,
    8: 6,
    9: 6,
    10:7,
    11:7
}
# Semitone -> interval quality.
INTERVAL_QUALITY = {
    0: "P",
    1: "m",
    2: "M",
    3: "m",
    4: "M",
    5: "P",
    6: "d",
    7: "P",
    8: "m",
    9: "M",
    10:"m",
    11:"M"
}

class Interval(Integral):
    """
    Interval : Integral

    Custom integer denoting an interval in semitones.
    """
    @staticmethod
    def from_name(name):
        """
        from_name(name)

        name : str →  A string of the form "qn", where
                q = p or P → perfect
                    u or U → unison
                    d or D → diminished
                    a or A → augmented
                    m → minor (moll)
                    M → major (dur)
                and
                n → a positive number

        Returns the corresponding interval, or None if `name` is malformed.

        e.g. Interval.from_name("p12")
                Returns an interval of one octave and perfect fifth, ascending.
             -Interval.from_name("M3")
                Returns a descending major third (note the minus sign).
        """
        try:
            quality, number = name[0], int(name[1:])
        except:
            return None
        if number <= 0:
            return None
        if number == 1:
            if quality.lower() not in ["p", "u", "a"]:
                return None
            return Interval({"p": 0, "u": 0, "a": 1 }[quality.lower()])
        octaves, sn = divmod(number - 1, 7)
        if sn in [0, 3, 4]:
            if quality.lower() not in ["p", "a", "d"]:
                return None
            shift = {"p": 0, "d": -1, "a": 1}[quality.lower()]
            st = {0: 0, 3: 5, 4: 7}[sn] + 12*octaves
            return Interval(st+shift)
        else:
            if quality.lower() not in ["a", "d", "m"]:
                return None
            shift = {"d": -2, "a": 1}.get(quality.lower(), 0) \
                + {"m": -1, "M": 0}.get(quality, 0)
            st = {1: 2, 2: 4, 5: 9, 6:11}[sn] + 12*octaves
            return Interval(st+shift)

    def __str__(self):
        if self.n < 0:
            neg = "-"
            val = -self.n
        else:
            neg = ""
            val = self.n
        octave, ic = divmod(val, 12)
        if octave == 0 and ic == 0:
            return "U1"
        else:
            return neg + INTERVAL_QUALITY[ic] + str(INTERVAL_NUMBER[ic]+7*octave)

    def _2json(self):
        return { "iv" : str(self) }

class IntervalClass(Z12, Interval):
    """
    IntervalClass : Z12, Interval

    An element of Z12 dentoing an interval class mod 1 octave.
    """
    @staticmethod
    def from_name(name):
        """
        from_name(name)

        Constructs an interval class out of `name` in the same way as in
        the Interval type.
        """
        iv = Interval.from_name(name)
        return IntervalClass(iv) if iv is not None else None

    def _2json(self):
        return { "ic" : str(self) }

    def __str__(self):
        if self.n == 0:
            return "P8"
        else:
            return Interval.__str__(self)

# Semitone -> pitch class w/o accidentals.
BASE_NAMES = {
    0 : "C",
    1 : "C",
    2 : "D",
    3 : "D",
    4 : "E",
    5 : "F",
    6 : "F",
    7 : "G",
    8 : "G",
    9 : "A",
    10 : "A",
    11 : "B",
}

class PitchClass(Torsor(Z12)):
    """
    PitchClass(n, acc) : Torsor(Z12)

    A set of pitch classes acted upon by the group of interval classes (which
    is Z12 in other guise). Carries separate information about the base pitch
    class and attached accidentals to be consistent when displaying output.
    (E.g. C## + M3 = E##.)
    """
    def __init__(self, n, acc=0):
        super().__init__(n)
        self.acc = acc

    @staticmethod
    def from_name(name):
        """
        from_name(name)

        name : str →  A case-insensitive string of the form "pa", where
                p → one of the pitch classes (ABCDEFG, without german H)
                a → a series of
                    "s" or "#" → sharps, or
                    "b" → flats.

        Returns a corresponding pitch class, or None if `name` is malformed.

        e.g. PitchClass.from_name("C##bb##bb")
                Returns C natural.
             PitchClass.from_name("C") + M3
                Returns E natural.
        """
        name = name.lower()
        name_map = {
            'c' : 0,
            'd' : 2,
            'e' : 4,
            'f' : 5,
            'g' : 7,
            'a' : 9,
            'b' : 11
            }
        shift = 0
        while len(name) > 1:
            mod = name[-1]
            if mod == 's' or mod == '#':
                shift+= 1
            elif mod == 'b':
                shift-= 1
            else:
                return None
            name = name[:-1]
        if name in name_map:
            accidental = shift
            if shift >= 0 and name_map[name] not in [4,11]:
                accidental-= 1
            return PitchClass(name_map[name] + shift, acc=accidental)
        else:
            return None
    
    def __add__(self, s):
        return PitchClass(self.v + s, self.acc)
    def __sub__(self, s):
        return PitchClass(self.v - s, self.acc)

    def __str__(self):
        shifted = (self.value - self.acc) % 12
        shnum   = int(shifted in [1,3,6,8,10]) + self.acc
        sharps  = "#"*shnum if shnum >= 0 else "b"*(-shnum)
        return BASE_NAMES[shifted] + sharps

    @property
    def accidental(self):
        return "#"*self.acc if self.acc >= 0 else "b"*(-self.acc)
    @accidental.setter
    def accidental(self, n):
        """
        self.accidental = n

        Changes the accidental of a given PitchClass `self`. The argument `n`
        can be either a string of accidentals as in `from_name`, or an integer
        denoting the total number of sharps (when `n`>0) or flats (if `n`<0).
        """
        if isinstance(n, basestring):
            acc = 0
            while n:
                if n[0] == "b":
                    acc-= 1
                elif n[0] in ["s", "#"]:
                    acc+= 1
                n = n[1:]
        else:
            acc = int(n)
        self.acc = acc
        
    def __repr__(self):
        return "PitchClass({}, {})".format(self.value, self.acc)
    def _2json(self):
        return {"pc" : str(self)}

class MIDInn(Integral):
    """
    MIDInn : Integral

    A 7-bit positive integer denoting a MIDI note number. The integer 69
    corresponds to concert A4 (440 Hz). A unit increment raises the pitch by
    one semitone.
    """
    @staticmethod
    def from_name(name):
        """
        from_name(name)

        name : str →  A case-insensitive string of the form "po", where
                p → a valid PitchClass name
                o → an integer (octave number)

        Returns a MIDInn corresponding to a given PitchClass-octave pair, or
        None if `name` is malformed.

        e.g. MIDInn.from_name("C4")
                Returns 60.
             MIDInn.from_name("Es-1")
                Returns 5.
        """
        idx = 0
        for i in range(len(name)-1,-1,-1):
            if name[i] not in "0123456789":
                idx = i
                break
        try:
            if name[idx] == "-":
                idx-= 1
            pc = PitchClass.from_name(name[:idx+1])
            pcv = pc.value
            pca = pc.acc
            octave = int(name[idx+1:]) - (pcv-pca)//12
        except:
            return None
        return MIDInn(60+int(pc) + (octave-4)*12)

    @classmethod
    def norm(cls, n):
        return 0 if n<0 else 127 if n>127 else n

    def __str__(self):
        octave = 4+(self.n-60)//12
        pc = PitchClass(self.n-60)
        return str(pc)+str(octave)

    def _2json(self):
        return { "nn": self.n }

# Predefined variables
Cb = PitchClass(11,-1) # enharmonic
C  = PitchClass(0)
Cs = PitchClass(1)
Db = PitchClass(1, -1)
D  = PitchClass(2)
Ds = PitchClass(3)
Eb = PitchClass(3, -1)
E  = PitchClass(4)
Es = PitchClass(5, 1)
Fb = PitchClass(4, -1)
F  = PitchClass(5)
Fs = PitchClass(6)
Gb = PitchClass(6, -1)
G  = PitchClass(7)
Gs = PitchClass(8)
Ab = PitchClass(8, -1)
A  = PitchClass(9)
As = PitchClass(10)
Bb = PitchClass(10, -1)
B  = PitchClass(11)
Bs = PitchClass(0, 1)

U1 = Interval(0)
m2 = Interval(1)
M2 = Interval(2)
m3 = Interval(3)
M3 = Interval(4)
P4 = Interval(5)
d5 = Interval(6)
P5 = Interval(7)
m6 = Interval(8)
M6 = Interval(9)
m7 = Interval(10)
M7 = Interval(11)
P8 = Interval(12)
m9 = Interval(13)
M9 = Interval(14)
m10 = Interval(15)
M10 = Interval(16)
P11 = Interval(17)
D12 = Interval(18)
P12 = Interval(19)
m13 = Interval(20)
M13 = Interval(21)
m14 = Interval(22)
M14 = Interval(23)
P15 = Interval(24)

P8c = IntervalClass(0)
m2c = IntervalClass(1)
M2c = IntervalClass(2)
m3c = IntervalClass(3)
M3c = IntervalClass(4)
P4c = IntervalClass(5)
d5c = IntervalClass(6)
P5c = IntervalClass(7)
m6c = IntervalClass(8)
M6c = IntervalClass(9)
m7c = IntervalClass(10)
M7c = IntervalClass(11)

# All MIDInn, with (double) flat/sharp enharmonics, e.g. C4, Esm1
for c in "CDEFGAB":
    for a in ["bb", "b", "", "s", "ss"]:
        for o in range(-1, 10):
            nm = c+a+str(o)
            nn = MIDInn.from_name(nm)
            globals()[nm.replace("#", "s").replace("-","m")] = nn

#=-
# Data i/o.

class Score:
    """
    Score(other, name, **settings)

    A data structure which stores the results of a single game session, along
    with the date the game was played, name and settings of the game. Can be
    exported to/imported from json.

    The results are stored as a mapping:
        <question-data>
            → (<# of correct answers>, <# of total occurences of the question>)

    where <question-data> is a tuple of objects uniquely identifying the
    question asked.

    E.g. in the case of TransposeGame, where the goal is to guess the result
    of a transposition of some pitch class by a given interval, <question-data>
    is a triple consisting of the initial pitch class, an interval by which the
    pitch class is transposed, and the direction of the transposition
    (ascending/descending). Note that questions with the same content are
    treated as the same question.
    """

    def __init__(self, other = None, name = None, **settings):
        self.settings = dict()
        self.name = ""
        if other is not None:
            if isinstance(other, Score):
                self.name = other.name
                self.start_date = other.start_date
                self.end_date = other.end_date
                self.data = other.data.copy()
                self.settings = other.settings.copy()
            elif isinstance(other, dict):
                self.name = other["score"]
                self.start_date = datetime.fromisoformat(other["start"])
                self.end_date = datetime.fromisoformat(other["end"])
                self.settings = other["settings"]
                self.data = dict((tuple(k), tuple(v)) for k,v in other["data"])
        else:
            self.start_date = None
            self.end_date = None
            self.data = dict()
        self.settings.update(settings)
        if name is not None:
            self.name = name

    def _store(self, ok, data):
        """
        _store(ok, data)

        If the answer was correct (`ok`==True), increments the correct answer
        count corresponding to the question-data `data` returned by
        Game._gen() while carrying a tally of the total number of answers.
        """
        if data in self.data:
            c,t = self.data[data]
            self.data[data] = (c+int(ok), t+1)
        else:
            self.data[data] = (int(ok), 1)

    def __add__(self, score):
        """
        self + score

        Constructs a summary of two games: `self` and `score`.
        """
        sc2 = Score(self, name = "Total")
        sc2+= score
        return sc2

    def __iadd__(self, score):
        """
        self+= score

        Updates `self` with data from the game `score`.
        """
        cond = self.start_date is None
        cond = cond or (score.start_date is not None and 
            self.start_date > score.start_date)
        if cond:
            self.start_date = score.start_date

        cond = self.end_date is None
        cond = cond or (score.end_date is not None and 
            self.end_date < score.end_date)
        if cond:
            self.end_date = score.end_date

        for k, v in score.data.items():
            if k in self.data:
                c,t = self.data[k]
                self.data[k] = (c+score.data[k][0], t+score.data[k][1])
            else:
                self.data[k] = score.data[k]
        self.settings = dict()
        return self

    def _smack(self):
        """
        _smack()

        Mark the start/end date of a game.
        """
        if self.start_date is None:
            self.start_date = datetime.now()
        elif self.end_date is None:
            self.end_date = datetime.now()

    def total(self, *cols):
        """
        total(*args)

        A method which computes the summarized results of the session.
        Returns the total amount of correct answers and the total number of
        answers among the questions whose succesive elements `d[n]` of their
        data-tuples correspond to their respective positional arguments in the
        following way.

        Each argument `x` can be either:
            → `None`,
            → a container (an object `x` which satisfies `cont(x) == True`,
            → or a value (not a container).
        If `x == args[n]` and:
            → not cont(x)
                ... then, only the questions which satisfy `d[n] == x`
                are counted in the tally.
            → cont(x)
                ... then only the questions which satisfy `d[n] in x`
                are counted in the tally.
            → x is None
                ...then the actual value of `d[n]` does not matter during
                the count.
        """
        totc, tott = 0,0
        for k,v in self.data.items():
            ok = True
            for i,c in enumerate(cols):
                if c is None:
                    pass
                elif not (cont(c) and k[i] in c) and (k[i] != c):
                    ok = False
                    break
            if ok:
                totc+= v[0]
                tott+= v[1]
        return totc, tott

    def questions(self):
        """
        questions()

        Returns an iterator over the session's question-data.
        """
        return self.data.keys()

    def _2json(self):
        return { "score": self.name,
            "start": self.start_date.isoformat(),
            "end": self.end_date.isoformat(),
            "settings": self.settings,
            "data": [ (k,v) for k,v in self.data.items() ]
            }

    # Helper functions for concatenating scores.
    @staticmethod
    def sum_settings_simple(scores, setting):
        ctr = None
        for sc in scores:
            ctr, ctrp = sc.settings.get(setting, None), ctr
            if ctrp is not None and ctr != ctrp:
                ctr = None
                break
        return ctr

    @staticmethod
    def sum_settings_list(scores, setting, sort_key):
        elems = set()
        for sc in scores:
            elems.update(sc.settings.get(setting, []))
        return sorted(list(elems), key = sort_key)

    @staticmethod
    def sum_scores(scores, score_name="Total", **settings):
        sc0 = Score(name = score_name)
        for sc in scores:
            sc0+= sc
        return Score(sc0, **settings)

def json_dec_hook(dct):
    if 'ic' in dct:
        return IntervalClass.from_name(dct["ic"])
    elif 'iv' in dct:
        return Interval.from_name(dct["iv"])
    elif 'pc' in dct:
        return PitchClass.from_name(dct["pc"])
    elif 'nn' in dct:
        return MIDInn(dct["nn"])
    elif 'score' in dct:
        return Score(dct, name=dct["score"])
    else:
        return dct

#=-
# Games

class Game:
    """
    Game(name=None, autosave=True, **settings)

    An abstract base class for Q&A games centered around intervals and pitch
    classes.

    Arguments:
        → name : str
            A name under which the game will be saved (in the "./stats"
            directory) as a `.json` file. If not given, a default name is
            used.
        → autosave : bool
            If `True`, saves the results to a `.json` file at the end of each
            game.
        → settings
            Game-specific settings.

    How to play:
        → Initialize the game.
            g = ————————Game("game-name", setting1=foo, setting2=bar, ...)
        → Press `play`.
            g.play(number_of_questions)
        → Answer the questions with strings recognized by the `from_name`
          methods of the expected data type.
        → Control the game with ?-commands (type `?help` at the answer prompt
          to see their list).
    """
    NAME = "Game"

    def __init__(self, name=None, autosave=True, **kwargs):
        self.name = name if name is not None else self.NAME
        self.fn = "./stats/" + self.name + ".json"
        self.autosave = bool(autosave)
        try:
            self.load(self.fn)
            settings = self._cur_score.settings.copy()
            settings.update(kwargs)
        except FileNotFoundError:
            self.scores = []
            settings = kwargs
        self.set_settings(**settings)

    def save(self, fn=None):
        """
        save(fn=None)

        Saves the game to the file `fn` or, if `fn` is not specified, to the
        default file ("./stats/`name`.json").
        """
        with open(fn if fn is not None else self.fn, "w+") as fh:
            json.dump(self.scores, fh, default = lambda obj: obj._2json())

    def load(self, fn):
        """
        load(fn)

        Loads the settings and scores of the current game from the file `fn`.
        """
        with open(fn, "r") as fh:
            self.scores = json.load(fh, object_hook=json_dec_hook)
        self._cur_score = self.scores[-1]

    def set_settings(self, **settings):
        """
        set_settings(**kwds)

        A function which changes given settings. The keyword arguments are
        exactly as in the initialization procedure.
        """
        raise NotImplementedError

    def _reset(self, session_name=None, **settings):
        """
        _reset(session_name, **kwds)

        Resets the current `Score`. Sets its name to `session_name` if given.
        """
        if session_name is None:
            session_name = self.name + " " + str(len(self.scores))
        self._cur_score = Score(name = session_name, **settings)

    def _gen(self):
        """
        _gen()

        Generates question parameters. The expected return value
        is
            dict(param_name1 = param1, param_name2 = param2, ...).
        """
        raise NotImplementedError()

    def _exercise(self, **data):
        """
        _exercise(**data)

        Asks questions according to question parameters `data`
        yielded by `_gen()`, accepts user's input and computes the right
        answer. The expected return value is a triple `(inp, ans, cor)`,
        where
            inp → raw user input,
            ans → the interpreted answer, which will be compared with `cor`,
            cor → the correct answer, of the same type as `ans`.
        """
        raise NotImplementedError()

    def play(self, n, session = None):
        """
        play(n, session)

        Starts a game session named `session` consisting of `n` questions,
        where `n` is a positive integer.

        Each question consists of a text or audio cue, after which the program
        awaits user input. An input beginning with `?` is a query and is not
        treated as an answer. The possible queries are:
            → ?quit : forces the session to end prematurely,
            → ?where : prints the current question number,
            → ?stats : prints a summary of the current game session,
            → ?again : repeats the question,
            → ?help : prints other available queries.
        """
        self._reset(session_name = session)
        self._cur_score._smack() # Set start time
        enough = False

        for i in range(n):
            wrong = False
            data = self._gen()
            inp, ans, corr = self._exercise(**data)
            while ans != corr:
                if inp[0] == "?":
                    if inp == "?quit":
                        enough = True
                        break
                    elif inp == "?where":
                        print(" ...we're at {}/{}.".format(i+1,n))
                    elif inp == "?stats":
                        self.summary(self._cur_score)
                        print()
                    elif inp == "?again":
                        pass
                    elif inp == "?debug":
                        print("... {}".format(data))
                    elif inp == "?help":
                        print("...other commands: ?again ?stats ?where ?quit")
                    else:
                        print("...unknown command.")
                elif ans is None:
                    print(" ...what? Could you repeat please?")
                else:
                    print(" ...no! Again.")
                    wrong = True
                inp, ans, corr = self._exercise(**data)
            if ans == corr:
                print(" ...ok" + (" (+1)" if not wrong else ""))
                self._store(not wrong, **data)
            if enough:
                break

        print("")
        self._cur_score._smack() # Set end time
        self.summary(self._cur_score)
        self.scores.append(self._cur_score)
        if self.autosave:
            self.save()

    def _store(self, ok, **data):
        """
        _store(ok, **data)

        Updates the correct answer count of the current game using
        `self._cur_score.store` of the class `Score`.

        Arguments:
            → ok : bool
                Is the answer correct?
            → data : dict()
                Question parameters returned by _gen().
        """
        raise NotImplementedError()
    
    def summary(self, score):
        """
        summary(score)
        
        Prints a summary of the given `score`.
        """
        self.details(score)

    def details(self, score, **query):
        """
        details(score, **query)

        Prints more details about the given `score` according to the stated
        `query`.

        The form of the parameter `query` is game-dependent and is specified
        in the documentation of each game.
        """
        self._print_game(score)
        if len(score.data) > 0:
            self._print_keys(score, self._details(score, **query))

    # Implementation details
    def _details(self, score, **query):
        """
        _details(score, **query)

        The implementation-dependent part of the `details` method. Transforms
        `query` into an iterator which yields successive `score` keys to be
        used in `score.total()` tagged with a display name. The output should
        have the form `(name, param)`.

        Used in `_print_keys` under the variable name `keys`.
        """
        raise NotImplementedError()

    # Summary-printing helper functions
    #
    # A generic summary:
    #
    #       ↓ <_print_game>
    #
    #   :: transpose-cof 1 :: dd.mm.yyyy 20:10 --> dd.mm.yyyy 20:13 :: 19/20 ::
    #   P4 [########################] 9/9
    #   P5 [#####################   ] 10/11
    #
    #       ↑ <_print_keys>
    #
    # A slice of `_print_keys`:
    #
    #   P5 [#####################   ] 10/11
    #   ↑ <name>   ↑ <_print_bar>    <c>/<t> = <score.data[actual_key]>

    def _print_bar(self, c, t):
        """
        _print_bar(c,t)

        Prints a partially filled bar depicting the ratio between the integers
        `c` and `t`.
        """
        MAXLEN = 24
        filled = c*MAXLEN//t
        rest = MAXLEN - filled
        return str("["+"#"*filled+" "*rest+"]")
    
    def _print_game(self, score):
        """
        _pring_game(score)

        Prints the first line of the `score` summary containing the general
        game data, such as name or dates.
        """
        ok, total = score.total()
        if score.start_date is not None:
            st = score.start_date.strftime("%d.%m.%Y %H:%M")
        else:
            st = "..."
        if score.end_date is not None:
            ed = score.end_date.strftime("%d.%m.%Y %H:%M")
        else:
            ed = "..."
        print(":: {} :: {} --> {} :: {}/{} ::".format(score.name,
            st, ed, ok, total) )

    def _print_keys(self, score, keys):
        """
        _print_keys(score, keys)

        Prints the correct/total answer count corresponding
        to question-data produced by the iterator `keys`
        – a return value of `_details(score, query)` – one
        per line, preformatted with `_print_bar`.
        """
        # keys = { ... (name, actual_key), ... }
        pdata = []
        maxlen = 0
        for key in keys:
            maxlen = max(maxlen, len(key[0]))
            c, t = score.total(*(key[1]))
            if t > 0:
                pdata.append( (key[0], c,t) )
        for nm, c, t in pdata:
            print(("{:<"+str(maxlen)+"} {} {}/{}").format(
                nm, self._print_bar(c,t), c, t)
            )

    # `Score`-getters.
    @property
    def latest(self):
        """
        latest()

        Gets the latest game's `Score`.
        """
        if self._cur_score is not None:
            return self._cur_score
        else:
            return Score(name="N/A")

    def select_total(self, frm=None, to=None, **kwargs):
        """
        select_total(frm=None, to=None)

        Obtains the total `Score` of the games played in the time
        interval from `frm` to `to`. Omitting an argument makes the
        interval unbounded in the corresponding direction.
        """
        f = datetime.min if frm is None else frm
        t = datetime.max if to is None else to
        scores = [ sc for sc in self.scores if sc.start_date >= f and
                sc.end_date <= t ]
        return self._sum_scores(scores)

    def select_first_after(self, frm=None, **kwargs):
        """
        select_first_after(frm=None)

        Obtains the `Score` of the first game played not earlier than `frm`.
        Omitting an argument chooses the earliest recorded game.
        """
        f = datetime.min if frm is None else frm
        scores = [ sc for sc in self.scores if sc.start_date >= f]
        return scores[0] if len(scores) > 0 else Score(name="N/A")

    def select_last_before(self, to=None, **kwargs):
        """
        select_last_before(to=None)

        Obtains the `Score` of the last game played not later than `to`.
        Omitting an argument chooses the latest recorded game.
        """
        t = datetime.max if to is None else to
        scores = [ sc for sc in self.scores if sc.end_date <= t]
        return scores[-1] if len(scores) > 0 else Score(name="N/A")

    def _sum_scores(self, scores):
        """
        _sum_scores(scores)

        A hook for `Score.sum` if preprocessing of `scores` is required. It is
        often the case if e.g. the game settings stored in the score need
        updating/merging during the concatenation.
        """
        return sum(scores)

# Score iterator/normalizer
def normalized_product(*args):
    """
    normalized_product(*args)

    A function that accepts
      → direct (non-container) arguments, which are treated 
          as 1-element lists, or
      → containers with valid `Score.total` arguments.

    It returns an iterator traversing the cartesian product of the
    containers given in the arguments and yielding the corresponding
    tuples of arguments which are subsequently normalized and are ready
    to be passed to `Score.total` as a compound question-data.

    This means that if, for example, `score.questions()` yields pairs of
    PitchClass and Interval, and the sorted lists of all PitchClasses/Intervals
    occurring among them are [P4,P5], [C,D] respectively, then:
        → normalized_product(P4, C) yields
            ([P4], [C]),
              which, when passed to `score.total`, returns
              the correct/total ratio of questions with parameters
              P4, C only.
        → normalized_product([P4,P5],[C,D]) yields
            ([P4],[C]),
            ([P4],[D]),
            ([P5],[C]),
            ([P5],[D]),
              which, when passed to 'score.total`, yields
              correct/total ratios of individual pairs.
        → normalized_product([[P4,P5]],None) yields
            ([P4,P5], None),
              which, when passed to `score.total`, yields
              c/t ratios of all questions with the first parameter being
              one of P4 and P5, and with any second parameter whatsoever.
        → normalized_product([[P4,P5], P4, P5],None) yields
            ([P4,P5], None),
            ([P4], None),
            ([P5], None),
              which acts as above in succession.
    """
    args = [ [a] if not isinstance(a,list) else a for a in args ]
    for vals in product(*args):
        vals2 = [ [v] if v is not None and not cont(v) else v
            for v in vals ]
        yield tuple(vals2)

# Sample settings for the TransposeGame.
ic_set_perfects = [P4,P5]
ic_set_thirds = [m3,M3]
ic_set_sixths = [m6,M6]
ic_set_leaps = [m3,M3,m6,M6]
ic_set_all = [m2,M2,m3,M3,P4,d5,P5,m6,M6,m7,M7,P8]

pc_set_diatonic = [C,D,E,F,G,A,B]
pc_set_with_sharps = [C,Cs,D,Ds,E,F,Fs,G,Gs,A,As,B]
pc_set_with_flats = [C,Db,D,Eb,E,F,Gb,G,Ab,A,Bb,B]
pc_set_all = [Cb,C,Cs,Db,D,Ds,Eb,E,Es,Fb,F,Fs,Gb,G,Gs,Ab,A,As,Bb,B,Bs]

class TransposeGame(Game):
    """
    TransposeGame(name=None, autosave=True, **settings) : Game

    A game to practice transposing pitch classes along ascending or descending
    intervals. The answers are passed to `PitchClass.from_name()` before
    evaluation.

    Sample question:
        C# + P5 = ?
        >> Gs (...ok! (+1))

    Game settings:
        → intervals : list of Interval or IntervalClass
            A list of intervals chosen at random by the game. (See the above
            examples.)
        → asc_desc  : str
            Whether the intervals chosen are ascending ("+"), descending ("-"),
            or both ("+-").
        → pitches   : list of PitchClass
            A list of pitch classes chosen at random by the game.

    Question data:
        (pc, ad, ic), where
            → pc → pitch class
            → ad → ascending / descending
            → ic → interval class

    `details` queries:
        Combinations of the following query arguments can be passed to the
        `details` method.

        → "intervals"...
            = "full" (DEFAULT)
                Lists the correct/total ratios for each interval stored in the
                game settings separately.
            = None
                Lists the sum of correct/total answers with respect to
                all intervals.
            = at most twice nested lists of Intervals, e.g.
                → P5
                    Lists only the results concerning the P5 interval.
                → [P4, P5]
                    Lists the results concerning the P4 and P5 interval
                    separately.
                → [P4, [M3, m3]]
                    Lists the results concerning the P4 interval, and then
                    lists the total results concerning minor and major thirds.
                → [[P4, P5]]
                    Lists the total results concerning the perfect intervals.
        → "asc_desc"...
            = "full" or "+-"
                Lists the correct/total ratios for ascending and descending
                intervals separately.
            = None (DEFAULT)
                Lists the sum of correct/total answers without discerning
                ascending or descending intervals.
            = "+"/"-"
                Lists the data only for ascending/descending intervals
                respectively.
        → "pitches"...
            = "full"
                Lists the correct/total ratios for each pitch class stored in
                the game settings separately.
            = None (DEFAULT)
                Lists the sum of correct/total answers with respect to
                all pitch classes.
            = at most twice nested lists of PitchClasses, e.g.
                → C
                    Lists only the results concerning the C note.
                → [C, D]
                    Lists the results concerning the C and D notes separately.
                → [C, [F, G]]
                    Lists the results concerning the C note, and then lists the
                    total results concerning both F and G notes.
                → [[F, G]]
                    Lists the total results concerning the F and G notes.

        All of the above queries are based on the `normalized_product`
        iterator. The process of parsing nested lists is explained in the
        documentation of the this function. See also help-strings for
        `Score`, `Score.total` and `Game._print_keys`.
    """
    NAME = "Transpose" # default name
    
    def __init__(self, *args, **kwargs):
        # init defaults
        self.icset = ic_set_all
        self.pcset = pc_set_all
        self.ad = [-1,1]
        # call parent, which loads previous settings,
        # overwrites some of them with user-provided kwargs,
        # and delegates initialization to set_settings with overwritten
        # settings
        super().__init__(*args, **kwargs)

    def set_settings(self, intervals=None, pitches=None,
            asc_desc=None, **settings):
        self.icset = intervals if intervals is not None else self.icset
        self.pcset = pitches if pitches is not None else self.pcset
        if asc_desc is not None:
            self.ad = []
            self.ad.append(-1) if "-" in asc_desc else None
            self.ad.append(1) if "+" in asc_desc else None
        if not self.ad:
            self.ad = [-1, 1]

    @property
    def intervals(self):
        return self.icset
    @intervals.setter
    def intervals(self, ic):
        self.icset = ic

    @property
    def pitches(self):
        return self.pcset
    @pitches.setter
    def pitches(self, pc):
        self.pcset = pc

    def _reset(self, session_name=None, **settings):
        dct = {-1: "-", 1: "+"}
        ad = "".join(sorted([dct[x] for x in self.ad]))
        # this passes the **settings as the last argument, effectively
        # overwriting the default settings inherited from `self` when not left
        # out in keyword arguments.
        super()._reset(session_name,
                intervals = self.icset,
                pitches = self.pcset,
                asc_desc = ad)

    def _gen(self):
        return {
            "pc": random.choice(self.pcset),
            "ic": random.choice(self.icset),
            "ad": random.choice(self.ad)
        }

    def _exercise(self, pc, ic, ad, **data):
        sgn = "+" if ad == 1 else "-"
        inp = input("{} {} {} = ".format(pc, sgn, ic))
        ans = PitchClass.from_name(inp)
        ic  = IntervalClass(ic)
        correct = pc + ic*ad
        return inp, ans, correct
    
    def _store(self, ok, pc, ic, ad, **data):
        sgn = "+" if ad == 1 else "-"
        self._cur_score._store(ok, (pc,sgn,ic))

    def _details(self, score, asc_desc=None, pitches=None, **query):
        # prepare args
        if "intervals" not in query or query["intervals"]=="full":
            if "intervals" in score.settings:
                intervals = list(score.settings["intervals"])
            else:
                intervals = {q[2] for q in score.questions()}
                intervals = sorted(list(intervals), key = lambda v: v.value)
        else:
            intervals = query["intervals"]
        if pitches=="full":
            if "pitches" in score.settings:
                pitches = list(score.settings["pitches"])
            else:
                pitches = {q[0] for q in score.questions()}
                pitches = sorted(list(pitches), key = lambda v: v.value)
        if asc_desc in ["+-", "full"]:
            asc_desc = ["+", "-"]

        # prepare names
        for pc, ad, ic in normalized_product(pitches, asc_desc, intervals):
            name = ""
            ispc = pc is not None and len(pc) == 1 and \
                    isinstance(pc[0], PitchClass)
            isic = ic is not None and len(ic) == 1 and \
                    isinstance(ic[0], Interval)
            isad = ad is None or (isinstance(ad, list) and
                    all(pm in ad for pm in ("+", "-")) )
            if ispc:
                name += str(pc[0])
            if isad and ispc and isic:
                name += "+-"
            elif ad is not None and ad[0] in ["+", "-"]:
                name += ad[0]
            if isic:
                name += str(ic[0])
            yield (name, (pc,ad,ic))

    def _sum_scores(self, scores):
        by_val = lambda x: x.value
        pcs = Score.sum_settings_list(scores, "pitches", by_val)
        ics = Score.sum_settings_list(scores, "intervals", by_val)
        ad = Score.sum_settings_simple(scores, "asc_desc")
        return Score.sum_scores(scores, self.name+ ": Total",
                pitches=pcs, intervals=ics, asc_desc=ad)
