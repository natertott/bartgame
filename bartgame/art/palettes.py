"""BARTGAME palettes. 16 colors each; index 0 is transparent for sprites
and the backdrop color for BG palette 0.

The look: Excalibur's emerald wood and chrome, Zelda's clean saturated
ramps. Every material has a dark outline hue (never pure black), three
or four body tones and one gleam. Shadows lean blue, lights lean gold.
All values are multiples of 8 so they survive the GBA's 5-bit channels.
"""

BG_PALETTES = [
    # 0 forest ground: grass, soil, blight, rot, a pale gleam
    ('forest', ['#000000',
                '#102018',   # 1 outline, deep shadow
                '#205838',   # 2 grass deep
                '#307840',   # 3 grass dark
                '#48a050',   # 4 grass mid
                '#70c060',   # 5 grass light
                '#a0e078',   # 6 grass bright
                '#503020',   # 7 soil dark
                '#805838',   # 8 soil mid
                '#b08858',   # 9 soil light
                '#381050',   # A blight deep
                '#702898',   # B blight mid
                '#b858e0',   # C blight bright
                '#788820',   # D rot dark
                '#c8e048',   # E rot bright
                '#fff0b0']), # F pale gold gleam
    # 1 wood: canopy walls, trees, thorns, stumps
    ('wood', ['#000000',
              '#081810',     # 1 outline
              '#103828',     # 2 leaf deepest
              '#185840',     # 3 leaf dark
              '#288050',     # 4 leaf mid
              '#48a860',     # 5 leaf light
              '#80d078',     # 6 leaf bright
              '#301808',     # 7 bark dark
              '#583420',     # 8 bark mid
              '#886040',     # 9 bark light
              '#b89060',     # A bark highlight
              '#602880',     # B thorn violet
              '#d070d0',     # C thorn pink
              '#48a050',     # D grass showing through (forest 4)
              '#200830',     # E blight black-violet
              '#f8e078']),   # F gold mote
    # 2 stone: rocks, ruins, pillars, water, chests, doors, torches, bones, gold
    ('stone', ['#000000',
               '#101820',    # 1 outline
               '#283048',    # 2 stone deep
               '#485068',    # 3 stone dark
               '#707c90',    # 4 stone mid
               '#a0acb8',    # 5 stone light
               '#d8e0e8',    # 6 stone bright, bone
               '#184878',    # 7 water deep
               '#2878b8',    # 8 water mid
               '#58b0e0',    # 9 water light
               '#c0f0ff',    # A water foam
               '#885818',    # B gold dark, wood shadow
               '#e0b030',    # C gold mid
               '#fff0a0',    # D gold bright, flame
               '#50a050',    # E moss on stone
               '#a06838']),  # F wood
    # 3 sewer: wet stone, slime, black water, rust, torchlight
    ('sewer', ['#000000',
               '#080c14',    # 1 outline
               '#182030',    # 2 stone deepest
               '#283448',    # 3 stone dark
               '#405068',    # 4 stone mid
               '#607890',    # 5 stone light
               '#90a8b8',    # 6 stone bright
               '#287828',    # 7 slime dark
               '#48b040',    # 8 slime mid
               '#90e860',    # 9 slime bright
               '#081018',    # A water black
               '#102838',    # B water dark
               '#2a5a70',    # C water glint
               '#8a4820',    # D rust
               '#f0a030',    # E flame
               '#fff0a0']),  # F flame bright, gold
    # 4 HUD and text
    ('hud', ['#000000',
             '#f8f0d8',      # 1 ink cream
             '#302018',      # 2 ink shadow
             '#e03040',      # 3 heart red
             '#ff7080',      # 4 heart bright
             '#801828',      # 5 heart dark
             '#886018',      # 6 gold dark
             '#e8b838',      # 7 gold mid
             '#fff0a8',      # 8 gold bright
             '#8890a0',      # 9 grey
             '#201828',      # A frame dark
             '#a0c8ff',      # B pale blue
             '#603890',      # C violet
             '#b080e0',      # D light violet
             '#100c18',      # E box fill
             '#404858']),    # F slate
]

OBJ_PALETTES = [
    # 0 hero: stalk greens, petal reds, a pale face, chrome and gold
    ('hero', ['#000000',
              '#0c1a10',     # 1 outline
              '#1e5a30',     # 2 stalk deep
              '#2e8040',     # 3 stalk dark
              '#48b050',     # 4 stalk mid
              '#80d868',     # 5 leaf light
              '#8a1020',     # 6 petal deep
              '#e03040',     # 7 petal red
              '#ff7868',     # 8 petal bright
              '#ffc0a8',     # 9 petal glow
              '#c0a870',     # A face shadow
              '#f0e0b0',     # B face
              '#405068',     # C steel dark
              '#a8c0d8',     # D steel light
              '#f0f8ff',     # E steel gleam
              '#f8d050']),   # F gold
    # 1 effects and pickups: sparks, hearts, gilt, keys, seeds
    ('fx', ['#000000',
            '#180c18',       # 1 outline
            '#901020',       # 2 red dark
            '#e83040',       # 3 red
            '#ff8080',       # 4 red bright
            '#885818',       # 5 gold dark
            '#e0b030',       # 6 gold mid
            '#fff0a0',       # 7 gold bright
            '#ffffff',       # 8 white
            '#4a2888',       # 9 violet dark
            '#8a60d8',       # A violet
            '#c8b0ff',       # B violet light
            '#383848',       # C grey dark
            '#7a7a90',       # D grey
            '#c0c0d0',       # E grey light
            '#c8e048']),     # F chartreuse
    # 2 bugs: beetle, bat, slime (violet chitin, chartreuse eyes, teal jelly)
    ('bugs', ['#000000',
              '#100818',     # 1 outline
              '#2a1840',     # 2 chitin deep
              '#482870',     # 3 chitin dark
              '#7040a8',     # 4 chitin mid
              '#a070d8',     # 5 chitin light
              '#d8b0ff',     # 6 chitin gleam
              '#88a020',     # 7 eye dark
              '#d0f040',     # 8 eye bright
              '#f8ffc0',     # 9 eye glow
              '#801828',     # A red dark
              '#e03048',     # B red
              '#186860',     # C jelly deep
              '#30b0a0',     # D jelly
              '#80f0d8',     # E jelly light
              '#e8e8f0']),   # F bone white
    # 3 blight: spitter, boss (sick greens, raw flesh, violet, bone)
    ('blight', ['#000000',
                '#141408',   # 1 outline
                '#304010',   # 2 sick deep
                '#507020',   # 3 sick dark
                '#80a830',   # 4 sick mid
                '#b8d848',   # 5 sick light
                '#e8f888',   # 6 sick bright
                '#500818',   # 7 flesh deep
                '#901030',   # 8 flesh dark
                '#d82850',   # 9 flesh
                '#ff6080',   # A flesh light
                '#ffb0c0',   # B flesh pale
                '#401058',   # C violet dark
                '#9038c0',   # D violet
                '#f0e0c0',   # E bone pale
                '#ffffff']), # F white
    # 4 iron: thorn knights and their swords (chrome plate, crimson, gold)
    ('iron', ['#000000',
              '#101420',     # 1 outline
              '#283048',     # 2 steel deep
              '#4a5878',     # 3 steel dark
              '#8090b0',     # 4 steel mid
              '#c0d0e8',     # 5 steel light
              '#f0f8ff',     # 6 steel gleam
              '#601020',     # 7 crimson dark
              '#c02038',     # 8 crimson
              '#301848',     # 9 violet dark
              '#6838a0',     # A violet
              '#f0c8a0',     # B skin
              '#b08060',     # C skin shadow
              '#906018',     # D gold dark
              '#f8d050',     # E gold
              '#ff4040']),   # F eye glow
    # 5 folk: the five NPCs (violet, crimson and green cloth, skin, silver)
    ('folk', ['#000000',
              '#101018',     # 1 outline
              '#302050',     # 2 violet deep
              '#6040a0',     # 3 violet
              '#a080e0',     # 4 violet light
              '#701020',     # 5 crimson dark
              '#d03040',     # 6 crimson
              '#206030',     # 7 green dark
              '#48a050',     # 8 green
              '#503018',     # 9 brown dark
              '#906038',     # A brown
              '#b08060',     # B skin shadow
              '#f0c8a0',     # C skin
              '#c0d0e0',     # D silver
              '#fffff0',     # E white
              '#f8d050']),   # F gold
]
