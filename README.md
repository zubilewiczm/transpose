# transpose

A simple, console-based quiz game written in Python 3.x that aims to improve your music-related arithmetic skills and your ears.

### Contents
`transpose.py` → text only games,
`transpose-alsaseq.py` → text and MIDI-based games.

The second file requires a working Linux ALSA MIDI setup, a MIDI (soft)synth and the [`alsaseq`](https://github.com/ppaez/alsaseq) package to work.

`pip install alsaseq`

### How to play?
1. Download the files and put them into a single directory. Run python in interactive mode and load one of the scripts.
`python -i transpose.py` or
`python -i transpose-alsaseq.py`

2. After loading the second one, connect the `pyTranspose` ALSA-MIDI output to a MIDI synth of your choice.

3. Choose one of the available games.
- `TransposeGame` : guess the result of transposing a pitch class by a given interval,
- `IntervalsGame` : guess the interval played via MIDI.

4. Run `——————Game` by initializing the corresponding object and typing "play":
```python
x = 20
g = TransposeGame("my_game_name",
		intervals = [m3, M3, P4, P5],
		pitches = pcs_all,
		acs_desc = "+-")
g.play(x)
```

You'll have to answer `x` questions by entering your guesses in the input prompts. To see what kind of answers are valid, read the help-string for your game and search for `from_name` within the sources. You can also begin your answer with a question mark to manage the game from inside the prompt – type `?help` to see all available commands.

When the session ends, its summary is displayed and your score is saved in the `./stats` directory (which has to be created beforehand!). If you quit your game and later reload it with the same name, your previous settings and acheivments are automatically restored. This can be done manually with

`g.save("my_game.json")`
`g.load("my_game.json")`

You can track your progress using

`g.summary(score)`, or
`g.details(score, intervals=[P4, P5], asc_desc="+")`,

where `score` can be obtained with one of

`score = g.latest`,
`score = g.select_first_after(datetime.today() - timedelta(days=1))`,
`score = g.select_last_before(datetime(2021, 4, 19))`,
`score = g.select_total(frm = datetime(2021, 4, 19), to = datetime.today() - timedelta(days=1))`.

That's about all there is to it. Have fun!

#### More info can be found in the files themselves.

Skim through the source files to find out how the game really works and how to extend or modify it to your liking.
