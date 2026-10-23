"""BARTGAME palettes. 16 colors each; index 0 is transparent for sprites
and the backdrop color for BG palette 0.

The look, from the concept boards: grime and glamour. Deep saturated
greens, teal water that glows, amber lantern light, warm grey-brown
stone, violet blight with magenta cracks, gold frames. Every material
has a dark hue outline, three or four body tones and a gleam. Values
are multiples of 8 so they survive the GBA's 5-bit channels.
"""

GRASS_MID = '#44a046'

BG_PALETTES = [
    # 0 forest ground: grass, paths, flowers, a blight stain, a gold mote
    ('forest', ['#000000',
                '#0c1a14',   # 1 outline, deep shadow
                '#1a5a3a',   # 2 grass deep
                '#2a7a3c',   # 3 grass dark
                GRASS_MID,   # 4 grass mid
                '#6cc050',   # 5 grass light
                '#a8e060',   # 6 grass bright
                '#6a4a28',   # 7 path dark
                '#a07a40',   # 8 path mid
                '#d0aa64',   # 9 path light
                '#58a8ff',   # A flower blue
                '#ff80c0',   # B flower pink
                '#fff8e0',   # C cream, white petals, bone
                '#7030b0',   # D blight violet
                '#d060f0',   # E blight magenta
                '#ffe070']), # F gold mote
    # 1 wood: canopy, trees, stumps, thorns, fences, logs, bridges, lanterns
    ('wood', ['#000000',
              '#081410',     # 1 outline
              '#0c3024',     # 2 leaf deepest
              '#145838',     # 3 leaf dark
              '#1e8048',     # 4 leaf mid
              '#3aa858',     # 5 leaf light
              '#78d070',     # 6 leaf bright
              '#3a2210',     # 7 bark dark
              '#6a4020',     # 8 bark mid
              '#a06838',     # 9 bark light
              '#d09858',     # A bark highlight
              '#c06020',     # B lantern amber dark
              '#ffb040',     # C lantern amber
              '#fff0a0',     # D lantern bright
              GRASS_MID,     # E grass showing through
              '#d060f0']),   # F thorn magenta
    # 2 stone: rocks, cliffs, ruins, water, gates, chests, torches, statues
    ('stone', ['#000000',
               '#101820',    # 1 outline
               '#2c3040',    # 2 stone deep
               '#4c5060',    # 3 stone dark
               '#787c88',    # 4 stone mid
               '#aab0b8',    # 5 stone light
               '#e0e4e8',    # 6 stone bright
               '#103a7a',    # 7 water deep
               '#1c64c0',    # 8 water mid
               '#40a8e8',    # 9 water light
               '#c8f4ff',    # A water foam
               '#8a5c18',    # B gold dark, wood shadow
               '#e8b838',    # C gold mid
               '#fff4b0',    # D gold bright, flame
               GRASS_MID,    # E moss, grass showing through
               '#a06838']),  # F wood
    # 3 blight: the deep rooms, purple ground, crystals, dead trees
    ('blight', ['#000000',
                '#100818',   # 1 outline
                '#24103c',   # 2 blight deepest
                '#3c1860',   # 3 blight deep
                '#6428a0',   # 4 blight mid
                '#9848d8',   # 5 blight light
                '#d868f8',   # 6 magenta glow
                '#f8b0ff',   # 7 pink bright
                '#1c1018',   # 8 dead bark dark
                '#3a2830',   # 9 dead bark
                '#5c4048',   # A dead bark light
                '#c090ff',   # B crystal light
                '#2a7a3c',   # C grass dark
                GRASS_MID,   # D grass mid
                '#ffe070',   # E gold mote
                '#ffffff']), # F white
    # 4 sewer: wet stone, moss, teal water, rust, candlelight
    ('sewer', ['#000000',
               '#0a0c12',    # 1 outline
               '#1c2028',    # 2 stone deepest
               '#343842',    # 3 stone dark
               '#555a64',    # 4 stone mid
               '#808690',    # 5 stone light
               '#b0b6bc',    # 6 stone bright
               '#2a6a30',    # 7 moss dark
               '#58a848',    # 8 moss light
               '#0c3a3c',    # 9 water deep teal
               '#188878',    # A water teal
               '#30c8b0',    # B water light teal
               '#b8f8f0',    # C water foam
               '#a05828',    # D rust, copper
               '#ffb040',    # E candle amber
               '#fff0a0']),  # F candle bright, gold
    # 5 sewer props: barrels, crates, bone, banners, awnings, the rug; 5 and F
    #   are the floor's stone tones so props sit on flagstones
    ('props', ['#000000',
               '#0a0c12',    # 1 outline
               '#3a2410',    # 2 wood dark
               '#6a4420',    # 3 wood mid
               '#a07040',    # 4 wood light
               '#555a64',    # 5 stone mid (the floor it stands on)
               '#e8e0c8',    # 6 bone
               '#a09880',    # 7 bone shadow
               '#146860',    # 8 banner teal dark
               '#28a898',    # 9 banner teal
               '#80201c',    # A red dark
               '#c83830',    # B red
               '#e8b838',    # C gold
               '#4c1c78',    # D rug violet dark
               '#8838c8',    # E rug violet
               '#808690']),  # F stone light (the floor's lit edges)
    # 6 HUD and text
    ('hud', ['#000000',
             '#f8f0d8',      # 1 ink cream
             '#2a1c10',      # 2 ink shadow
             '#e82838',      # 3 heart red
             '#ff7878',      # 4 heart bright
             '#801020',      # 5 heart dark
             '#8a5c18',      # 6 gold dark
             '#e8b838',      # 7 gold mid
             '#fff4b0',      # 8 gold bright
             '#8890a0',      # 9 grey
             '#161020',      # A frame fill
             '#38a0ff',      # B blue
             '#1848a0',      # C blue dark
             '#9040d8',      # D violet
             '#0c0a14',      # E box fill
             '#3a3a48']),    # F slate, empty
]

OBJ_PALETTES = [
    # 0 hero: petals, a cream face, hood greens, leather, steel, gold
    ('hero', ['#000000',
              '#1a0c10',     # 1 outline
              '#b02818',     # 2 petal deep
              '#f04828',     # 3 petal red
              '#ff8030',     # 4 petal orange
              '#ffb048',     # 5 petal light tip
              '#fff8e8',     # 6 face cream
              '#e8c8a0',     # 7 face shadow
              '#1c4a28',     # 8 tunic deep
              '#2e8040',     # 9 tunic green
              '#58b858',     # A tunic light
              '#5a3418',     # B leather dark
              '#9a6030',     # C leather light
              '#b8c8d8',     # D steel
              '#f8fcff',     # E steel gleam
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
            '#58c8ff']),     # F blue glow
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
    # 5 folk: the Peddler's purple hide and red hood, the Gatekeeper's hat
    ('folk', ['#000000',
              '#100c14',     # 1 outline
              '#5a3878',     # 2 purple hide dark
              '#8a60b0',     # 3 purple hide
              '#c8a888',     # 4 pale skin shadow
              '#f0dcc0',     # 5 pale skin
              '#801c1c',     # 6 red dark
              '#d03030',     # 7 red
              '#3c1c68',     # 8 violet dark
              '#6c38b0',     # 9 violet
              '#a068e0',     # A violet light
              '#f0c040',     # B gold
              '#906018',     # C gold dark
              '#f0f0f8',     # D white, silver
              '#7a4a24',     # E brown
              '#48a050']),   # F green
    # 6 portraits: faces for the dialogue box
    ('portrait', ['#000000',
                  '#100c14', # 1 outline
                  '#b02818', # 2 petal deep
                  '#f04828', # 3 petal red
                  '#ff8030', # 4 petal orange
                  '#fff8e8', # 5 face cream
                  '#e8c8a0', # 6 face shadow
                  '#2e8040', # 7 green
                  '#8a60b0', # 8 purple hide
                  '#5a3878', # 9 purple hide dark
                  '#d03030', # A red
                  '#801c1c', # B red dark
                  '#6c38b0', # C violet
                  '#b0a0d0', # D lavender, steel
                  '#f0c040', # E gold
                  '#ffffff']), # F white
    # 7 ui sprites: the mini-map
    ('ui', ['#000000',
            '#161020',       # 1 dark
            '#e8d8a8',       # 2 parchment
            '#b8a070',       # 3 parchment dark
            '#8a5c18',       # 4 gold dark
            '#e8b838',       # 5 gold
            '#fff4b0',       # 6 gold bright
            '#2a6a30',       # 7 green dark
            '#58a048',       # 8 green
            '#f03030',       # 9 red dot
            '#ffffff',       # A white
            '#38a0ff',       # B blue
            '#8890a0',       # C grey
            '#3a3a48',       # D slate
            '#ff80c0',       # E pink
            '#ffe070']),     # F gold mote
]
