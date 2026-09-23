"""Render the small, exact teaching diagrams used by the foundations chapter."""
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parents[1] / 'assets/foundations'
OUT.mkdir(parents=True, exist_ok=True)
INK, GREEN, ORANGE, MUTED = '#243b2e', '#326b50', '#bd6c3e', '#6e766d'

def text(x, y, value, size=17, color=INK, anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(str(value))}</text>'

def box(x, y, label, width=130, height=52, fill='#edf3e9', color=GREEN):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{fill}" stroke="{color}"/>' + text(x+width/2, y+height/2+6, label, anchor='middle')

def arrow(x1, y1, x2, y2, color=GREEN):
    return f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="2" marker-end="url(#arrow)"/>'

def row(values, y, start=95, gap=135):
    return ''.join(box(start+i*gap, y, value, 100) for i,value in enumerate(values))

def save(name, title, subtitle, body, footer):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="380" viewBox="0 0 760 380" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle + '. ' + footer)}</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10" fill="{GREEN}"/></marker></defs>
<style>text{{font-family:ui-sans-serif,-apple-system,Segoe UI,Arial,sans-serif}}</style>
<rect width="760" height="380" rx="14" fill="#fafbf7" stroke="#d6ded0"/>
{text(30,42,title,23)}{text(30,70,subtitle,14,MUTED)}
{body}
<path d="M30 320H730" stroke="#d6ded0"/>{text(30,350,footer,15,MUTED)}
</svg>'''
    (OUT / f'{name}.svg').write_text(svg)

save('cost','Count work before timing it','Doubling the input from 8 to 16 items',
     text(42,115,'One scan')+box(245,87,'8 visits')+arrow(390,113,450,113)+box(475,87,'16 visits')+
     text(42,195,'Every pair')+box(245,167,'28 pairs')+arrow(390,193,450,193)+box(475,167,'120 pairs')+
     text(42,276,'A scan doubles. Pair comparisons grow much faster.',18),
     'Time counts operations; extra space counts additional retained state.')
save('sequences','A slice owns a half-open range','[start, end) includes start and excludes end',
     row([10,20,30,40],125)+''.join(text(145+i*135,113,i,14,MUTED,'middle') for i in range(4))+
     '<path d="M230 190V205H465V190" fill="none" stroke="#bd6c3e" stroke-width="3"/>'+
     text(347,240,'values[1:3] → [20, 30]',20,ORANGE,'middle')+text(347,277,'length = end − start = 2',16,MUTED,'middle'),
     'A Python list slice copies the selected entries; assignment shares the list.')
save('sets','Membership keeps one copy','Presence and frequency answer different questions',
     row(['A','A','B'],105,start=70)+arrow(465,130,540,130)+box(565,105,'{A, B}',135)+
     box(110,230,'A present? Yes',210)+box(400,230,'A count? Not stored',250),
     'Choose a counter when repeated occurrences change the answer.')
save('queues','Which work goes next?','The same arrivals A, B, C produce different removal orders',
     text(30,122,'FIFO queue',18)+row(['A','B','C'],140,start=190)+arrow(190,166,110,166)+text(42,204,'A leaves first',14,GREEN)+
     text(30,253,'LIFO stack',18)+row(['A','B','C'],235,start=190)+arrow(565,261,700,261)+text(555,308,'C leaves first',14,ORANGE),
     'FIFO explores a frontier; LIFO follows the newest unfinished branch.')
save('links','Keep the rest of the chain reachable','Save the next reference before replacing a link',
     box(80,130,'4')+arrow(213,156,307,156)+box(310,130,'9')+arrow(443,156,537,156)+box(540,130,'None')+
     text(145,115,'current',14,GREEN,'middle')+text(375,115,'following',14,ORANGE,'middle')+
     arrow(375,245,145,245)+text(260,276,'After reversal: 9 → 4 → None',19,INK,'middle'),
     'Object identity matters. Equal values can live in different nodes.')
save('trees','A tree carries inherited constraints','The left subtree of 5 must remain below 5 at every depth',
     box(320,90,'5',100)+arrow(338,142,236,190)+arrow(402,142,530,190)+
     box(170,190,'3',100)+box(490,190,'8',100)+arrow(265,228,352,270)+box(360,250,'6 ✕',100,48,'#f9eee7',ORANGE)+
     text(70,285,'6 > 3, but 6 is not < 5',17,ORANGE),
     'A parent comparison alone cannot validate a binary search tree.')
save('tries','A prefix is a path; a word has a marker','Insert car, card, and cat',
     box(35,160,'root',80)+arrow(115,186,155,186)+box(160,160,'c',70)+arrow(230,186,270,186)+box(275,160,'a',70)+
     arrow(345,179,435,122)+box(440,95,'r ●',90)+arrow(530,121,615,121)+box(620,95,'d ●',90)+
     arrow(345,193,435,253)+box(440,225,'t ●',90)+text(560,270,'● complete word',15,GREEN),
     'ca is a valid prefix; only terminal markers establish complete words.')
save('connectivity','Merge components as links arrive','Connectivity does not require storing a route',
     box(70,110,'{0, 1}',180)+box(470,110,'{2, 3}',180)+arrow(250,136,460,136)+text(350,116,'union(1, 2)',16,ORANGE,'middle')+
     arrow(350,164,350,224)+box(230,235,'{0, 1, 2, 3}',260)+text(360,309,'find(0) == find(3)',16,GREEN,'middle'),
     'A representative identifies the current component, not a stable business ID.')
save('pointers','Move a boundary only when order proves it safe','Sorted values [1, 3, 4, 8], target 7',
     row([1,3,4,8],125)+text(145,113,'left',14,GREEN,'middle')+text(550,113,'right',14,ORANGE,'middle')+
     arrow(550,190,415,190)+text(400,221,'1 + 8 is too large → move right inward',16,ORANGE,'middle')+
     arrow(145,250,280,250)+text(380,290,'1 + 4 is too small → move left; 3 + 4 = 7',17,INK,'middle'),
     'Without sorted order, these pointer movements can discard a valid answer.')
save('greedy','Earliest finish leaves room','Maximize the number of non-overlapping intervals',
     text(40,123,'long')+box(140,95,'[0, 6)',510,38,'#f9eee7',ORANGE)+
     text(40,196,'select')+box(225,166,'[1, 3)',170,38)+box(395,166,'[3, 5)',170,38)+
     text(110,258,'Two shorter intervals fit; one long interval blocks both.',18)+
     text(110,290,'Change the objective to weighted value and the proof changes.',14,MUTED),
     'A greedy rule needs a safety argument tied to the exact objective.')
save('bits','A mask selects independent flags','READ = 001, WRITE = 010, EXECUTE = 100',
     text(50,136,'READ | WRITE',17)+row([0,1,1],106,start=310,gap=100)+
     text(50,224,'& READ',17)+row([0,0,1],194,start=310,gap=100)+text(665,226,'→ true',16,GREEN)+
     text(310,287,'EXECUTE is not enabled.',17),
     'Compact representation does not remove exponential subset enumeration.')
save('selection','Start with the repeated question','Choose state that removes repeated work',
     box(45,108,'Remember',145)+box(220,108,'Order',145)+box(395,108,'Explore',145)+box(570,108,'Reuse',145)+
     text(117,202,'set / map',17,GREEN,'middle')+text(292,202,'sort / heap',17,GREEN,'middle')+
     text(467,202,'BFS / search',17,GREEN,'middle')+text(642,202,'DP / prefix',17,GREEN,'middle')+
     text(380,275,'Contract → invariant → cost → changed requirement',19,INK,'middle'),
     'Practice applies these tools; a refresher is there only when needed.')
save('weighted-paths','Fewest edges is not always cheapest','All weights here are nonnegative',
     box(80,120,'A',100)+box(555,120,'B',100)+arrow(185,146,550,146)+text(365,130,'cost 10',18,ORANGE,'middle')+
     box(320,240,'C',100)+arrow(180,169,318,254)+arrow(423,254,555,169)+
     text(205,235,'cost 1',16,GREEN,'middle')+text(520,235,'cost 1',16,GREEN,'middle')+text(370,309,'A → C → B costs 2',17,GREEN,'middle'),
     'The frontier prioritizes cost; best_cost rejects obsolete heap entries.')
save('sorting','Sort by a declared key','Stable sorting preserves arrival order among equal keys',
     row(['2 / A','1 / B','2 / C'],105,start=130)+arrow(380,167,380,220)+row(['1 / B','2 / A','2 / C'],235,start=130),
     'A and C share key 2; they keep their original relative order.')
print(f'Rendered {len(list(OUT.glob("*.svg")))} foundation diagrams')
