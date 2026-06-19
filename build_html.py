#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

import os
OUT=os.path.join(os.path.dirname(__file__),"index.html")
raw=json.load(open(os.path.join(os.path.dirname(__file__),"report_data.json")))
f=lambda x: float(x) if x not in (None,"") else 0.0

PARTNERS=[("varus","VARUS","VARUS"),("kopiyka","Копійка","KOPIYKA"),("loko","Локо","LOKO"),
          ("hophey","Hop Hey","HOP HEY"),("rukavychka","Rukavichka","RUKAVYCHKA"),("beermarket","Beer Market","BEER MARKET")]
MONTHS=["2026-01","2026-02","2026-03","2026-04","2026-05"]
MNAME={"2026-01":"Січень","2026-02":"Лютий","2026-03":"Березень","2026-04":"Квітень","2026-05":"Травень"}

def tmetrics(r,off):
    k=["gmv","impr","viewed","added","placed","delivered","ua_brand","ua_city","aov","basket","ret30","retsp"]
    return {k[i]:f(r[off+i]) for i in range(len(k))}

data={}
for r in raw["totals"]:
    g,ym=r[0],r[1]; m=tmetrics(r,2); m["stores"]=int(f(r[14]))
    data.setdefault(g,{}).setdefault(ym,{})["t"]=m
for r in raw["cities"]:
    g,ym,city=r[0],r[1],r[2]; m=tmetrics(r,3); m["city"]=city or "—"
    data.setdefault(g,{}).setdefault(ym,{}).setdefault("c",[]).append(m)
for r in raw["stores"]:
    g,ym,name,city=r[0],r[1],r[2],r[3]; m=tmetrics(r,4); m["name"]=name or "—"; m["city"]=city or "—"
    data.setdefault(g,{}).setdefault(ym,{}).setdefault("s",[]).append(m)
for r in raw["cons"]:
    g,ym=r[0],r[1]
    data.setdefault(g,{}).setdefault(ym,{})["cons"]={"orders":f(r[2]),"active":f(r[3]),"new":f(r[4])}

# assemble export structure keyed by partner key
DATA={"months":MONTHS,"mname":MNAME,"orientirAOV":18,
      "partners":[{"key":k,"display":d} for k,d,g in PARTNERS],"data":{}}
for k,d,g in PARTNERS:
    DATA["data"][k]=data.get(g,{})

TEMPLATE=r"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Партнерські огляди на Bolt Food — Україна</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root{--bg:#eef1f7;--panel:#fff;--line:#dfe5ee;--text:#13203a;--muted:#5d6b85;--soft:#33425d;
    --accent:#34b27a;--accent2:#0e8f5e;--info:#2563eb;--ok:#15a34a;--warn:#ea580c;}
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.5}
  nav.topnav{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.95);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
  nav.topnav .inner{max-width:1100px;margin:0 auto;padding:9px 20px;display:flex;flex-wrap:wrap;gap:7px;align-items:center}
  nav.topnav .brand{font-weight:800;font-size:13px;color:var(--accent2);margin-right:6px}
  .ptab{cursor:pointer;color:var(--muted);font-size:13px;font-weight:700;padding:6px 11px;border-radius:8px;border:1px solid transparent;text-decoration:none}
  .ptab:hover{background:#eef2f8;color:var(--text)}
  .ptab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
  nav .right{margin-left:auto}
  .dl{background:var(--accent);color:#fff;border:none;border-radius:8px;padding:8px 14px;font-weight:800;font-size:13px;cursor:pointer;font-family:inherit}
  .dl:hover{filter:brightness(1.06)}
  .wrap{max-width:1100px;margin:0 auto;padding:22px 20px 70px}
  .sheet{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:30px 36px;box-shadow:0 1px 4px rgba(20,40,80,.06)}
  h1{font-size:24px;margin:0 0 3px}
  .subtitle{color:var(--muted);font-size:13.5px;margin:0 0 6px}
  .tag{display:inline-block;font-size:11px;font-weight:700;color:var(--accent2);background:rgba(52,178,122,.12);border:1px solid rgba(52,178,122,.3);border-radius:6px;padding:2px 8px}
  h2{font-size:16px;margin:26px 0 9px;color:var(--accent2);border-bottom:1px solid var(--line);padding-bottom:5px}
  h3{font-size:13px;margin:14px 0 6px;color:var(--soft)}
  p{margin:6px 0;font-size:13.5px;color:var(--soft)}
  b{color:var(--text)}
  .months{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 4px}
  .mtab{cursor:pointer;font-size:12.5px;font-weight:700;padding:5px 12px;border-radius:20px;border:1px solid var(--line);background:#fafbfd;color:var(--muted)}
  .mtab.active{background:var(--info);color:#fff;border-color:var(--info)}
  .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;margin-top:14px}
  .kpi{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:#fafbfd}
  .kpi .v{font-size:20px;font-weight:800}
  .kpi .v.acc{color:var(--accent2)}.kpi .v.ok{color:var(--ok)}.kpi .v.info{color:var(--info)}.kpi .v.warn{color:var(--warn)}
  .kpi .l{font-size:11px;color:var(--muted);margin-top:2px}
  .chartbox{border:1px solid var(--line);border-radius:10px;padding:15px;background:#fff;margin-top:6px}
  .chartcap{font-size:11.5px;color:var(--muted);margin:6px 0 0}
  .callout{border-radius:10px;padding:12px 15px;margin:14px 0;font-size:13px;border:1px solid var(--line);border-left:4px solid var(--info);background:rgba(37,99,235,.05)}
  .callout.warn{border-left-color:var(--warn);background:rgba(234,88,12,.05)}
  .callout.acc{border-left-color:var(--accent);background:rgba(52,178,122,.06)}
  .callout b{color:var(--text)}
  table.dt{width:100%;border-collapse:collapse;margin-top:6px;font-size:12px}
  table.dt th,table.dt td{border:1px solid var(--line);padding:6px 8px;text-align:right}
  table.dt th{background:#f1f5fb;color:var(--muted);font-weight:700;font-size:11px;position:sticky;top:0}
  table.dt td:first-child,table.dt th:first-child{text-align:left;font-weight:700;color:var(--text)}
  table.dt tr:nth-child(even) td{background:#fafbfd}
  table.dt tr.total td{background:rgba(52,178,122,.10);font-weight:800;border-top:2px solid var(--accent)}
  .tblwrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin-top:6px}
  .footnote{font-size:11.5px;color:var(--muted);font-style:italic;margin-top:7px}
  .page{display:none}.page.active{display:block}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:15px}
  @media(max-width:760px){.kpis{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}.sheet{padding:18px}}
  @media print{
    @page{size:A4 portrait;margin:11mm}
    nav.topnav{display:none}.months{display:none}
    body{background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}
    .wrap{max-width:none;margin:0;padding:0}.sheet{border:none;box-shadow:none;border-radius:0;padding:0}
    .page{display:none!important}.page.active{display:block!important}
    h2{font-size:13.5px;break-after:avoid;page-break-after:avoid}
    .kpi,.chartbox,.callout,.kpis{break-inside:avoid;page-break-inside:avoid}
    .chartbox canvas{max-height:300px}
    .tblwrap{overflow:visible;border:none}
    table.dt{font-size:8.6px}table.dt thead{display:table-header-group}
    table.dt tr{break-inside:avoid;page-break-inside:avoid}
    table.dt th,table.dt td{padding:3px 5px}
    canvas{max-width:100%!important}
  }
</style>
</head>
<body>
<nav class="topnav"><div class="inner" id="ptabs">
  <span class="brand">Bolt Food · Партнери</span>
  <span class="right"><button class="dl" onclick="window.print()">Зберегти сторінку у PDF</button></span>
</div></nav>
<div class="wrap" id="pages"></div>
<script>
var DATA = /*DATA*/;
var _charts = {};
function mkChart(id,cfg){ var el=document.getElementById(id); if(!el) return; if(_charts[id]) _charts[id].destroy(); _charts[id]=new Chart(el,cfg); }
var PAL={accent:'#34b27a',info:'#2563eb',ok:'#15a34a',warn:'#ea580c',muted:'#5d6b85'};
Chart.defaults.font.family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif";
Chart.defaults.color=PAL.muted;
var fN=function(v){return Math.round(v).toLocaleString('en-US');};
var fE=function(v){return '€'+Math.round(v).toLocaleString('en-US');};
var fE2=function(v){return '€'+(v||0).toFixed(2);};
var pc=function(v){return (v==null||isNaN(v))?'—':Math.round(v)+'%';};
function rates(m){
  return {eng:m.viewed?m.added/m.viewed*100:null, conv:m.viewed?m.delivered/m.viewed*100:null,
          drop:m.added?(1-m.placed/m.added)*100:null};
}
function availMonths(key){ return DATA.months.filter(function(ym){var d=DATA.data[key][ym]; return d&&d.t&&d.t.gmv>0;}); }

function kpiBlock(t,cons){
  var freq = (cons&&cons.active)? (cons.orders/cons.active):null;
  var rep = (cons&&cons.active)? ((cons.active-cons.new)/cons.active*100):null;
  function k(v,l,c){return '<div class="kpi"><div class="v '+(c||'')+'">'+v+'</div><div class="l">'+l+'</div></div>';}
  return '<div class="kpis">'+
    k(fE(t.gmv),'Оборот (GMV) до знижок','acc')+
    k(fN(t.delivered),'Доставлені замовлення','ok')+
    k(fN(t.stores),'Активні заклади','')+
    k(fE2(t.aov),'Середній чек','')+
    k(cons?fN(cons.active):'—','Активні клієнти','info')+
    k(cons?fN(cons.new):'—','Нові клієнти','acc')+
    k(freq?freq.toFixed(2):'—','Частота (замовл./клієнт)','')+
    k(rep!=null?Math.round(rep)+'%':'—','Повторні клієнти','info')+
    '</div>';
}
function consBlock(t,cons){
  var r=rates(t);
  function k(v,l,c){return '<div class="kpi"><div class="v '+(c||'')+'">'+v+'</div><div class="l">'+l+'</div></div>';}
  return '<h2>Споживачі та залученість</h2><div class="kpis">'+
    k(pc(t.ret30),'Утримання 30 днів','info')+
    k(pc(t.retsp),'Повертаються до бренду (30д)','info')+
    k((t.basket||0).toFixed(1),'Товарів у кошику','')+
    k(pc(r.drop),'Відвал на етапі кошика','warn')+
    k(fN(t.impr),'Покази у застосунку','')+
    k(pc(r.eng),'Залученість меню','info')+
    k(pc(r.conv),'Конверсія (перегляд→замовл.)','ok')+
    k(fN(t.ua_brand),'Активацій (бренд)','acc')+
    '</div>';
}
function tableBlock(title,rows,isStore){
  var head = isStore
    ? ['Заклад (адреса)','Місто','Оборот €','Сер. чек €','Перегл. меню','Кошик','Доставлено','Залуч.','Конв.','Відвал кошика']
    : ['Місто','Оборот €','Сер. чек €','Перегл. меню','Кошик','Доставлено','Залуч.','Конв.','Відвал кошика'];
  rows.sort(function(a,b){return b.gmv-a.gmv;});
  var tot={gmv:0,viewed:0,added:0,delivered:0,placed:0,aovw:0,aovwt:0};
  var body=rows.map(function(m){
    var r=rates(m);
    tot.gmv+=m.gmv;tot.viewed+=m.viewed;tot.added+=m.added;tot.delivered+=m.delivered;tot.placed+=m.placed;
    var cells = isStore
      ? [stripName(m.name),m.city,fE(m.gmv),fE2(m.aov),fN(m.viewed),fN(m.added),fN(m.delivered),pc(r.eng),pc(r.conv),pc(r.drop)]
      : [m.city,fE(m.gmv),fE2(m.aov),fN(m.viewed),fN(m.added),fN(m.delivered),pc(r.eng),pc(r.conv),pc(r.drop)];
    return '<tr>'+cells.map(function(c){return '<td>'+c+'</td>';}).join('')+'</tr>';
  }).join('');
  var tr=rates(tot);
  var totAov = tot.delivered? tot.gmv/tot.delivered : 0;
  var totcells = isStore
    ? ['Разом','',fE(tot.gmv),fE2(totAov),fN(tot.viewed),fN(tot.added),fN(tot.delivered),pc(tr.eng),pc(tr.conv),pc(tr.drop)]
    : ['Разом',fE(tot.gmv),fE2(totAov),fN(tot.viewed),fN(tot.added),fN(tot.delivered),pc(tr.eng),pc(tr.conv),pc(tr.drop)];
  body += '<tr class="total">'+totcells.map(function(c){return '<td>'+c+'</td>';}).join('')+'</tr>';
  return '<h2>'+title+'</h2><div class="tblwrap"><table class="dt"><thead><tr>'+
    head.map(function(h){return '<th>'+h+'</th>';}).join('')+'</tr></thead><tbody>'+body+'</tbody></table></div>'+
    '<p class="footnote">Сер. чек — середній чек до знижок. Залуч. — перегляд меню→кошик. Конв. — перегляд меню→доставлене замовлення. Відвал кошика — частка сесій, де додали товар, але не оформили замовлення.</p>';
}
function stripName(n){ if(!n) return '—'; var i=n.indexOf(','); var j=n.indexOf('|');
  if(j>-1&&j<18) return n.slice(j+1).trim(); if(i>-1&&i<18) return n.slice(i+1).trim(); return n; }

function renderMonth(key, ym){
  var d=DATA.data[key][ym]; if(!d||!d.t){return '<p>Немає даних за цей місяць.</p>';}
  var t=d.t, cons=d.cons, r=rates(t);
  var disp=DATA.partners.filter(function(p){return p.key===key;})[0].display;
  var html='';
  html+='<h1>'+disp+' на Bolt Food — '+DATA.mname[ym]+' 2026</h1>';
  html+='<p class="subtitle">Огляд ефективності у розрізі міст і закладів</p><span class="tag">Підготовлено командою Bolt Food для '+disp+'</span>';
  html+=kpiBlock(t,cons);
  // drop-off callout
  if(r.drop!=null){
    html+='<div class="callout warn"><b>Відвал на етапі кошика:</b> '+Math.round(r.drop)+'% сесій, у яких клієнт додав товар у кошик, не завершилися замовленням. Це найближчий резерв: спрощення оформлення, нагадування про кинутий кошик, поріг безкоштовної доставки.</div>';
  }
  html+='<h2>Шлях клієнта</h2><div class="chartbox"><canvas id="fn-'+key+'" height="110"></canvas><p class="chartcap">Від перегляду меню до доставленого замовлення, '+DATA.mname[ym]+' 2026.</p></div>';
  html+=consBlock(t,cons);
  if(d.c&&d.c.length) html+=tableBlock('Деталізація за містами', d.c.slice(), false);
  if(d.s&&d.s.length) html+=tableBlock('Деталізація за закладами', d.s.slice(), true);
  return html;
}
function initMonthCharts(key, ym){
  var t=DATA.data[key][ym].t;
  mkChart('fn-'+key,{type:'bar',data:{labels:['Перегляд меню','Додано в кошик','Доставлено'],
    datasets:[{label:'Кількість',data:[Math.round(t.viewed),Math.round(t.added),Math.round(t.delivered)],backgroundColor:PAL.info,borderRadius:5,maxBarThickness:54}]},
    options:{indexAxis:'y',plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){return c.parsed.x.toLocaleString('en-US');}}}},
    scales:{x:{ticks:{callback:function(v){return v.toLocaleString('en-US');}}}}}});
}
function selectMonth(key, ym){
  document.getElementById('content-'+key).innerHTML = renderMonth(key, ym);
  initMonthCharts(key, ym);
  var mt=document.getElementById('months-'+key);
  Array.prototype.forEach.call(mt.children,function(b){b.classList.toggle('active', b.dataset.ym===ym);});
}

// ---- Comparison page ----
function seriesByMonth(metricFn){
  return DATA.partners.map(function(p){
    return {name:p.display, data:DATA.months.map(function(ym){var d=DATA.data[p.key][ym]; return (d&&d.t&&d.t.gmv>0)? metricFn(d):null;})};
  });
}
function renderCompare(){
  var html='<h1>Порівняння місяців — усі партнери</h1><p class="subtitle">Динаміка ключових показників, січень–травень 2026</p>';
  html+='<div class="grid2">'+
    '<div class="chartbox"><canvas id="cmp-gmv" height="150"></canvas><p class="chartcap">Оборот (GMV) до знижок, € за місяць</p></div>'+
    '<div class="chartbox"><canvas id="cmp-ord" height="150"></canvas><p class="chartcap">Доставлені замовлення за місяць</p></div>'+
    '<div class="chartbox"><canvas id="cmp-aov" height="150"></canvas><p class="chartcap">Середній чек, € за місяць</p></div>'+
    '<div class="chartbox"><canvas id="cmp-conv" height="150"></canvas><p class="chartcap">Конверсія (перегляд меню→замовлення), % за місяць</p></div>'+
    '<div class="chartbox"><canvas id="cmp-new" height="150"></canvas><p class="chartcap">Нові клієнти за місяць</p></div>'+
    '<div class="chartbox"><canvas id="cmp-ret" height="150"></canvas><p class="chartcap">Утримання 30 днів, % за місяць</p></div>'+
    '</div>';
  // latest-month comparison table (May)
  var ym='2026-05';
  html+='<h2>Порівняння за травень 2026</h2><div class="tblwrap"><table class="dt"><thead><tr>'+
    ['Партнер','Оборот €','Замовлення','Сер. чек €','Конв.','Відвал кошика','Активні клієнти','Нові','Частота','Утримання 30д']
    .map(function(h){return '<th>'+h+'</th>';}).join('')+'</tr></thead><tbody>';
  DATA.partners.forEach(function(p){
    var d=DATA.data[p.key][ym]; if(!d||!d.t){return;}
    var t=d.t,cons=d.cons,r=rates(t);
    var freq=(cons&&cons.active)?(cons.orders/cons.active).toFixed(2):'—';
    html+='<tr><td>'+p.display+'</td><td>'+fE(t.gmv)+'</td><td>'+fN(t.delivered)+'</td><td>'+fE2(t.aov)+'</td><td>'+pc(r.conv)+'</td><td>'+pc(r.drop)+'</td><td>'+(cons?fN(cons.active):'—')+'</td><td>'+(cons?fN(cons.new):'—')+'</td><td>'+freq+'</td><td>'+pc(t.ret30)+'</td></tr>';
  });
  html+='</tbody></table></div>';
  return html;
}
function initCompareCharts(){
  var labels=DATA.months.map(function(m){return DATA.mname[m];});
  function lc(id,series,suffix){
    mkChart(id,{type:'line',data:{labels:labels,datasets:series.map(function(s,i){
      var col=[PAL.accent,PAL.info,PAL.warn,PAL.ok,'#9333ea','#0891b2'][i%6];
      return {label:s.name,data:s.data,borderColor:col,backgroundColor:col,spanGaps:true,tension:.25};})},
      options:{plugins:{legend:{position:'top',labels:{boxWidth:10,font:{size:10}}}},
      scales:{y:{ticks:{callback:function(v){return suffix==='€'?'€'+v.toLocaleString('en-US'):(suffix==='%'?v+'%':v.toLocaleString('en-US'));}}}}}});
  }
  lc('cmp-gmv',seriesByMonth(function(d){return Math.round(d.t.gmv);}),'€');
  lc('cmp-ord',seriesByMonth(function(d){return Math.round(d.t.delivered);}),'');
  lc('cmp-aov',seriesByMonth(function(d){return +d.t.aov.toFixed(2);}),'€');
  lc('cmp-conv',seriesByMonth(function(d){return d.t.viewed?+(d.t.delivered/d.t.viewed*100).toFixed(1):null;}),'%');
  lc('cmp-new',seriesByMonth(function(d){return d.cons?Math.round(d.cons.new):null;}),'');
  lc('cmp-ret',seriesByMonth(function(d){return +(d.t.ret30||0).toFixed(1);}),'%');
}

// ---- build pages & tabs ----
(function(){
  var ptabs=document.getElementById('ptabs'), pages=document.getElementById('pages');
  var brand=ptabs.querySelector('.brand'), right=ptabs.querySelector('.right');
  DATA.partners.forEach(function(p,idx){
    var a=document.createElement('a'); a.className='ptab'+(idx===0?' active':''); a.textContent=p.display; a.dataset.go=p.key;
    ptabs.insertBefore(a, right);
    var months=availMonths(p.key);
    var page=document.createElement('div'); page.className='page'+(idx===0?' active':''); page.dataset.p=p.key;
    var sheet=document.createElement('div'); sheet.className='sheet';
    var mbar='<div class="months" id="months-'+p.key+'">'+months.map(function(ym,i){
      return '<span class="mtab'+(i===months.length-1?' active':'')+'" data-ym="'+ym+'" onclick="selectMonth(\''+p.key+'\',\''+ym+'\')">'+DATA.mname[ym]+'</span>';}).join('')+'</div>';
    sheet.innerHTML=mbar+'<div id="content-'+p.key+'"></div>';
    page.appendChild(sheet); pages.appendChild(page);
    p._defMonth=months.length?months[months.length-1]:null;
  });
  // compare tab
  var ac=document.createElement('a'); ac.className='ptab'; ac.textContent='Порівняння'; ac.dataset.go='compare';
  ptabs.insertBefore(ac,right);
  var cp=document.createElement('div'); cp.className='page'; cp.dataset.p='compare';
  var cs=document.createElement('div'); cs.className='sheet'; cs.id='content-compare'; cp.appendChild(cs); pages.appendChild(cp);

  function activate(key){
    Array.prototype.forEach.call(document.querySelectorAll('.page'),function(pg){pg.classList.toggle('active',pg.dataset.p===key);});
    Array.prototype.forEach.call(document.querySelectorAll('.ptab'),function(t){t.classList.toggle('active',t.dataset.go===key);});
    if(key==='compare'){ document.getElementById('content-compare').innerHTML=renderCompare(); initCompareCharts(); }
    else { var p=DATA.partners.filter(function(x){return x.key===key;})[0]; if(p._defMonth){selectMonth(key,p._defMonth);} }
    window.scrollTo(0,0);
  }
  Array.prototype.forEach.call(document.querySelectorAll('.ptab'),function(t){t.addEventListener('click',function(){activate(t.dataset.go);});});
  // initial render
  var first=DATA.partners[0]; if(first._defMonth){ selectMonth(first.key, first._defMonth); }
})();
</script>
</body>
</html>"""

html=TEMPLATE.replace("/*DATA*/", json.dumps(DATA, ensure_ascii=False, separators=(",",":")))
open(OUT,"w",encoding="utf-8").write(html)
print("written bytes:", len(html))
