from transpose import *
import alsaseq
import alsamidi
import random

# Requires https://github.com/ppaez/alsaseq package.
alsaseq.client("pyTranspose", 0, 1, True)

class IntervalsGame(Game):
    """
    IntervalsGame(name=None, autosave=True, **settings) : Game

    A game to practice recognizing asceending, descending or harmonic
    (simultaneous) intervals by ear. Requires a working MIDI setup.
    The answers are passed to `Interval.from_name()` before evaluation.

    Sample question:
        <a C4 note followed by a E4 note is played>
        >> M3 (...ok! (+1))

    Game settings:
        → intervals : list of Interval or IntervalClass
            A list of intervals chosen at random by the game.
        → adh : str
            Whether the intervals chosen are ascending ("a"), descending ("d"),
            or harmonic ("h"). Any combination of these letters makes the game
            choose one of the options at random (e.g. "ahh" chooses between
            ascending and harmonic intervals with 50:50 chance for each).
        → center : MIDInn
            Average MIDI note number that the game chooses as the first note
            of the interval.
        → spread : Integral
            Maximal difference (in semitones) between the first note of the
            interval played and the `center`.

    Question parameters:
        (ctr, itc, adh), where
            → ctr → first note of an interval
            → itc → the interval (determining the second note)
            → adh → ascending / descending / harmonic

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
        → "notes"...
            = "full"
                Lists the correct/total ratios for each note stored in
                the game settings separately.
            = None (DEFAULT)
                Lists the sum of correct/total answers with respect to
                all notes.
            = at most twice nested lists of MIDInn-s, e.g.
                → C4
                    Lists only the results concerning the note C4.
                → [C4, D4]
                    Lists the results concerning the C4 and D4 notes
                    separately.
                → [C4, [G3, G4]]
                    Lists the results concerning the C4 note, and then lists
                    the total results concerning both G notes.
                → [[G3, G4, G5]]
                    Lists the total results concerning the three G notes.
        → "asc_desc"...
            = "full" or "+-h"
                Lists the correct/total ratios for ascending, descending and
                harmonic intervals separately.
            = None (DEFAULT)
                Lists the sum of correct/total answers without discerning
                ascending, descending or harmonic intervals.
            = "+"/"-"/"h"
                Lists the data only for ascending/descending/harmonic intervals
                respectively.
            = "m"
                Lists the data concerning the melodic intervals, e.e. the
                totals for both ascending and descending ones.
            = "+-" or "-+"
            = "+h" or "+h"
            = "-h" or "h-"
            = "mh" or "hm"
                Applies the options corresponding to the above successively.
                
        All of the above queries are based on the `normalized_product`
        iterator. The process of parsing nested lists is explained in the
        documentation of the this function. See also help-strings for
        `Score`, `Score.total` and `Game._print_keys`.
    """
    NAME = "Intervals"
    
    def __init__(self, *args, **kwargs):
        self.icset = ic_set_all
        self.center = A4
        self.spread = 12
        self.adh = [-1,1]
        super().__init__(*args, **kwargs)

    def set_settings(self,
            intervals=None,
            center=None,
            spread=None,
            adh=None, **settings):
        self.icset = intervals if intervals is not None else self.icset
        self.spread = spread if spread is not None else self.spread
        if center is not None:
            self.center = MIDInn(center)
        if adh:
            self.adh = []
            self.adh.append(-1) if "d" in adh else None
            self.adh.append(0) if "h" in adh else None
            self.adh.append(1) if "a" in adh else None
        if not self.adh:
            self.adh = [-1,1]

    @property
    def intervals(self):
        return self.icset
    @intervals.setter
    def intervals(self, ic):
        self.icset = ic

    def _reset(self, session_name=None, **settings):
        dct = {-1: "d", 0: "h", 1: "a"}
        melo = "".join(sorted([dct[x] for x in self.adh]))
        super()._reset(session_name,
                intervals = self.icset,
                center = self.center,
                spread = self.spread,
                adh = melo)

    def _gen(self):
        lo, hi = self.center - self.spread, self.center + self.spread
        ctr = random.randint(lo, hi)
        itc = random.choice(self.icset)
        adh = random.choice(self.adh)
        if adh == 0: # harmonic
            # The correct answer is the interval measured upwards
            # Uniformize distribution by switching top note with bottom one
            #   randomly.
            if random.choice([True, False]):
                # e.g. 69+5 vs 69-5 ~=~ 64+5. Note 69 is played anyway.
                ctr-= int(itc)
        return { "ctr": MIDInn(ctr), "itc": itc, "adh": adh }

    def _exercise(self, ctr, itc, adh, **data):
        sgn = -1 if adh == -1 else 1

        self.play_notes(ctr, ctr+itc*sgn, (adh == 0))
        inp = input(">> ")

        ans = Interval.from_name(inp)
        correct = itc
        return inp, ans, correct

    @staticmethod
    def play_notes(note1, note2, simult):
        # Some human variation for parameters
        v1 = int(random.triangular(60,120))
        v2 = int(random.triangular(60,120))
        d1 = int(random.triangular(400,900))
        d2 = int(random.triangular(-200,200))
        if simult:
            of = int(random.triangular(0,70,0))
            note1,note2 = random.sample([note1,note2],2)
        else:
            of = d1+int(random.triangular(-100,500))
        ev1 = alsamidi.noteevent(0, int(note1), v1, 0, d1)
        ev2 = alsamidi.noteevent(0, int(note2), v2, of, d1+d2)
        # Play sequence
        alsaseq.start()
        alsaseq.output(ev1)
        alsaseq.output(ev2)
        alsaseq.syncoutput()
        alsaseq.stop()
    
    def _store(self, ok, ctr, itc, adh, **data):
        sgn = "+" if adh == 1 else "-" if adh == -1 else "h"
        self._cur_score._store(ok, (ctr,sgn,itc))

    def _details(self, score, adh=None, notes=None, **query):
        # prepare args
        if "intervals" not in query or query["intervals"]=="full":
            if "intervals" in score.settings:
                intervals = list(score.settings["intervals"])
            else:
                intervals = {q[2] for q in score.questions()}
                intervals = sorted(list(intervals), key = lambda v: v.value)
        else:
            intervals = query["intervals"]
        if notes=="full":
            notes = {q[0] for q in score.questions()}
            notes = sorted(list(notes), key = lambda v: v.value)
        if adh=="full":
            adh = ["+", "-", "h"]
        elif adh is not None:
            if "m" in adh:
                adh = adh.replace("+","m").replace("-","m")
            uniq = []
            for char in adh:
                if not char in uniq and char in "+-hm":
                    uniq.append(char)
            adh = [ ["+", "-"] if e == "m" else e for e in uniq]

        # prepare names
        for nn, ad, ic in normalized_product(notes, adh, intervals):
            namelist = []
            mode = ["+","-"] if ad is None else ad
            isnn = nn is not None and len(nn) == 1 and \
                    isinstance(nn[0], MIDInn)
            isic = ic is not None and len(ic) == 1 and \
                    isinstance(ic[0], Interval)
            if isnn:
                namelist += [str(nn[0])]
            namelist += ["".join(sorted(mode)).replace("+-", "m")]
            if isic:
                namelist += [str(ic[0])]
            name = " ".join(namelist)
            yield (name, (nn,mode,ic))

    def _sum_scores(self, scores):
        by_val = lambda x: x.value
        ics = Score.sum_settings_list(scores, "intervals", by_val)
        ctr = Score.sum_settings_simple(scores, "center")
        spr = Score.sum_settings_simple(scores, "spread")
        adh = Score.sum_settings_simple(scores, "adh")
        return Score.sum_scores(scores, self.name+": Total",
            intervals=ics, center=ctr, spread=spr, adh=adh)
