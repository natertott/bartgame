"""One native RGB555 palette vocabulary for the complete reboot."""
import reboot_core as R
import reboot_ui as U
import faces
import sewer_concepts as SC
import enemy_studies as ENEMY_STUDIES
import forest_concepts as FC

PACK_TILES=False
GRASS_MID=R.PALETTES['ground'][4]
BG_PALETTES=list(R.PALETTES.items())
for name in ('menu','map','hud'):
    BG_PALETTES.append((name,U.GROUPS[name]))
BG_PALETTES = FC.bg_palettes(BG_PALETTES)

# Keep physical OBJ slot names stable; every ink now comes from the same core.
OBJ_ALIASES=[('hero','hero'),('fx','gold'),('bugs','foliage'),('blight','blight'),
             ('iron','stone'),('folk','hero'),('portrait','hero'),('lift','stone'),
             ('ui','ui'),('gear','gold'),('items','gold'),('pick','gold'),
             ('icons','gold'),('peddler','gold'),('gatekeeper','stone'),('uikit','ui')]
OBJ_PALETTES=[(name,U.GROUPS[name] if name in U.GROUPS else R.PALETTES[material])
              for name,material in OBJ_ALIASES]
if ENEMY_STUDIES.VARIANT:
    import enemy_studies_palette
    # Every material-item frame has an explicit palette; their default slot10
    # is free in the playfield. Keep bugs2 exact for cloak/carried-bush art.
    OBJ_PALETTES=[(name,enemy_studies_palette.colors() if name=='items' else colors)
                  for name,colors in OBJ_PALETTES]
FACE_PALETTES=[['#000000']+['#%02x%02x%02x'%tuple(rgb) for _,rgb in palette]
               for _,palette,_ in faces.FACES]
if SC.VARIANT:
    import sewer_concepts_terrain as SCT
    import sewer_concepts_npcs as SCN
    BG_PALETTES=[(name,SCT.palette(SC.RECIPE['style']) if name=='drain' else colors)
                 for name,colors in BG_PALETTES]
    if SC.VARIANT == 9:
        import sewer_final as SF
        BG_PALETTES = [(name, SF.palette() if name == 'drain' else colors)
                       for name, colors in BG_PALETTES]
    OBJ_PALETTES=[(name,SCN.peddler_palette(SC.RECIPE['peddler']) if name=='peddler'
                  else SCN.wizard_palette(SC.RECIPE['wizard']) if name=='gatekeeper'
                  else colors) for name,colors in OBJ_PALETTES]
for name,colors in BG_PALETTES+OBJ_PALETTES:
    assert len(colors)==16,(name,len(colors))
    assert all(all(int(color[j:j+2],16)%8==0 for j in (1,3,5)) for color in colors),name
assert len(OBJ_PALETTES)<=16
