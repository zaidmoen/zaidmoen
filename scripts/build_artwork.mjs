// Rebuild the complete identity with Node.js 18+ and no dependencies
import { mkdirSync, writeFileSync } from 'node:fs';

const C = { ink: '#101214', panel: '#181B1E', gold: '#CDB583', bright: '#E9D7AF', text: '#F3F0E9', muted: '#A7A9AA', line: '#34383B' };
const esc = v => String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const text = (x,y,v,s=20,c=C.text,weight=400,extra='') => `<text x="${x}" y="${y}" font-family="Arial,Helvetica,sans-serif" font-size="${s}" fill="${c}" font-weight="${weight}" ${extra}>${esc(v)}</text>`;
const label = (x,y,v,c=C.gold,s=12) => text(x,y,v,s,c,500,'letter-spacing="2"');
const rect = (x,y,w,h,fill=C.panel,stroke='none') => `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="${stroke}"/>`;
const line = (d,c=C.line,w=1) => `<path d="${d}" fill="none" stroke="${c}" stroke-width="${w}"/>`;
const circle = (x,y,r,c=C.gold) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${c}"/>`;

// Two open angular strokes make a Z and M with a shared visual rhythm
const mark = (x,y,s=1,c=C.gold) => `<g transform="translate(${x} ${y}) scale(${s})" fill="none" stroke="${c}" stroke-width="10" stroke-linejoin="miter"><path d="M0 0H68L0 74H68"/><path d="M88 74V0L126 40 164 0V74"/></g>`;

function save(path,w,h,title,body,desc=title) {
  const file = new URL('../assets/'+path+'.svg',import.meta.url);
  mkdirSync(new URL('.',file),{recursive:true});
  writeFileSync(file,`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-labelledby="title desc"><title id="title">${esc(title)}</title><desc id="desc">${esc(desc)}</desc><defs><linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#8E774E"/><stop offset=".45" stop-color="#E9D7AF"/><stop offset="1" stop-color="#AD9464"/></linearGradient></defs>${rect(0,0,w,h,C.ink)}${body}${rect(.5,.5,w-1,h-1,'none',C.line)}</svg>\n`);
}

function emblem(cx,cy,scale=1) {
  let b='';
  for(let i=0;i<4;i++) b+=`<rect x="${-126-i*16}" y="${-126-i*16}" width="${252+i*32}" height="${252+i*32}" transform="rotate(45)" fill="none" stroke="${i===0?'#756546':C.line}" stroke-width="${i===0?1.5:1}"/>`;
  b+=line('M-285 0H-220M220 0H285M0-245V-220M0 220V245')+circle(-220,0,3)+circle(220,0,3);
  b+=mark(-98,-44,1.2,'url(#metal)');
  return `<g transform="translate(${cx} ${cy}) scale(${scale})">${b}</g>`;
}

function diagram(kind) {
  let b=rect(0,0,430,238,C.panel,C.line)+label(22,31,'SYSTEM / '+kind.toUpperCase(),C.muted,10)+line('M22 48H408');
  if(kind==='layers') {
    ['CONTROLLER','COMPONENT','REPOSITORY'].forEach((s,i)=>{
      const y=68+i*48;
      b+=rect(70,y,290,34,i===1?'#29271F':C.ink,i===1?C.gold:C.line)+text(215,y+22,s,12,i===1?C.bright:C.text,500,'text-anchor="middle" letter-spacing="2"');
      if(i<2)b+=line(`M215 ${y+34}v14`,C.gold);
    });
  } else if(kind==='membership') {
    b+=circle(73,98,18,C.gold)+line('M42 151v-12q31-36 62 0v12',C.gold,2);
    b+=line('M127 112H162',C.gold);
    b+=rect(179,73,223,55,C.ink,C.line)+label(195,95,'REGISTRATION',C.muted,10)+text(195,115,'Student membership',15);
    b+=rect(179,141,223,55,'#29271F',C.gold)+circle(196,169,4)+text(210,174,'Payment confirmed',15,C.bright);
    b+=line('M290 128v13',C.gold);
  } else {
    b+=rect(24,70,382,38,C.ink,C.line)+text(40,95,'query → tokenize → retrieve',16,C.text);
    ['INVERTED INDEX','POSITIONAL POSTINGS','PHRASE MATCH'].forEach((s,i)=>{
      b+=text(26,139+i*31,s,11,C.muted,400,'letter-spacing="1.5"');
      for(let j=0;j<4-i;j++)b+=rect(243+j*39,125+i*31,28,18,j===0?C.gold:'#42433C');
    });
  }
  return b;
}

const projects=[
  ['employee-hub','01','Employee Hub API','BACKEND ENGINEERING','Workforce operations, built in layers.','Django REST / SQLAlchemy / Marshmallow','layers'],
  ['nai-membership','02','NAI Membership','PRODUCT ENGINEERING','From student registration to membership.','Django / React / PostgreSQL','membership'],
  ['irforge','03','IRForge','INFORMATION RETRIEVAL','From a query to the right documents.','Python / Inverted index / Phrase search','search']
];

for(const mobile of [false,true]) {
  const w=mobile?600:1200, suffix=mobile?'-mobile':'', pad=mobile?32:48;
  let b=mark(pad,27,.3)+label(pad+69,44,'ZAID MAYYALLEH',C.text,11)+label(w-pad,44,'PALESTINE',C.muted,10).replace('<text ','<text text-anchor="end" ');
  b+=line(`M${pad} 72H${w-pad}`);
  b+=label(pad,mobile?118:128,'BACKEND ENGINEERING / APPLIED AI',C.gold,mobile?11:12);
  b+=text(pad-5,mobile?204:240,'Zaid',mobile?92:113,C.text,700,'letter-spacing="-5"');
  b+=text(pad-5,mobile?288:342,'Mayyalleh',mobile?78:100,C.text,700,'letter-spacing="-5"');
  b+=rect(pad,mobile?316:373,64,3,C.gold);
  b+=text(pad,mobile?358:420,'Thoughtful systems.',mobile?26:29,C.text);
  b+=text(pad,mobile?393:458,'Built with intent.',mobile?26:29,C.muted);
  b+=emblem(mobile?300:939,mobile?613:307,mobile?.76:.85);
  const baseline=mobile?848:538;
  b+=line(`M${pad} ${baseline}H${w-pad}`);
  b+=label(pad,baseline+31,'PYTHON / DJANGO / RELATIONAL DATA',C.muted,mobile?10:11);
  if(!mobile)b+=label(895,baseline+31,'LEARN. BUILD. REFINE.',C.gold,10);
  save('profile/hero'+suffix,w,mobile?902:594,'Zaid Mayyalleh — Backend engineering and applied AI',b,'Personal identity in charcoal and champagne gold. A geometric ZM monogram accompanies the name and the statement: Thoughtful systems. Built with intent.');

  for(const [slug,n,title,category,desc,stack,kind] of projects) {
    b=label(pad,43,n+' / '+category,C.gold,11)+text(w-pad,45,'↗',25,C.gold,400,'text-anchor="end"');
    b+=text(pad-2,mobile?105:117,title,mobile?40:49,C.text,700,'letter-spacing="-1.5"');
    b+=text(pad,mobile?142:159,desc,mobile?21:22,C.muted);
    if(mobile) {
      b+=`<g transform="translate(32 175) scale(1.2465)">${diagram(kind)}</g>`;
      b+=line('M32 496H568')+text(32,529,stack,18,C.text);
    } else {
      b+=line('M48 197H665')+text(48,232,stack,18,C.text)+label(48,280,'VIEW REPOSITORY',C.muted,10);
      b+=`<g transform="translate(722 69)">${diagram(kind)}</g>`;
    }
    save('featured/'+slug+suffix,w,mobile?562:337,title,b,desc+' '+stack+'. Conceptual illustration, not a product screenshot.');
  }

  b=label(pad,42,'THE TOOLKIT',C.gold,11);
  const groups=[['01','Languages',['Python · JavaScript · TypeScript','C++ · SQL']],['02','Web & backend',['Django · FastAPI · React','MySQL · Supabase']],['03','AI & workflow',['OpenCV · MediaPipe','scikit-learn · Git']]];
  groups.forEach(([n,title,items],i)=>{
    const x=mobile?32:48+i*376,y=mobile?77+i*155:79;
    b+=line(`M${x} ${y}H${x+(mobile?536:344)}`)+label(x,y+31,n,C.gold,11);
    b+=text(x+40,y+32,title,22,C.text,600);
    b+=text(x,y+77,items[0],mobile?22:18,C.muted)+text(x,y+108,items[1],mobile?22:18,C.muted);
  });
  save('profile/stack'+suffix,w,mobile?551:226,'Tools across projects and ongoing learning',b,'Languages, backend tools, computer vision and development workflow. Tools used and explored, not proficiency ratings.');

  b=rect(0,0,w,mobile?340:275,C.gold)+label(pad,43,"LET'S BUILD SOMETHING THAT MATTERS",C.ink,mobile?10:11);
  b+=text(pad-3,mobile?114:132,'Good ideas.',mobile?53:72,C.ink,700,'letter-spacing="-2"');
  b+=text(pad-3,mobile?176:211,'Thoughtful execution.',mobile?45:72,C.ink,700,'letter-spacing="-2"');
  b+=text(pad,mobile?223:248,'Internships · Junior roles · Collaboration',mobile?20:18,'#343128');
  b+=line(mobile?'M32 249H568':'M1010 78H1146', '#8A7958');
  b+=text(mobile?32:1010,mobile?290:113,'GET IN TOUCH',12,C.ink,700,'letter-spacing="1.5"');
  b+=text(w-pad,mobile?299:212,'↗',mobile?49:74,C.ink,400,'text-anchor="end"');
  save('profile/connect'+suffix,w,mobile?340:275,"Let's connect — Zaid Mayyalleh",b,'Open to internships, junior roles and collaboration. Contact Zaid by email.');
}

save('brand/monogram',400,400,'ZM — Zaid Mayyalleh',emblem(200,200,.64));
save('brand/wordmark',850,180,'Zaid Mayyalleh — wordmark',mark(40,54,.8)+line('M210 44V136')+text(248,101,'ZAID MAYYALLEH',37,C.text,600,'letter-spacing="3"')+label(250,130,'BACKEND ENGINEERING / APPLIED AI',C.gold,11));
console.log('Generated 14 profile and brand assets');
