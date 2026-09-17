// Generate self-contained profile SVGs. Node.js 18+, no dependencies.
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

function buildArtwork(){
const files={};const C={bg:"#080f20",panel:"#101b30",line:"#23334d",text:"#edf4ff",muted:"#a0b2cc",blue:"#7da8ff",cyan:"#67e8f9"};
const esc=s=>String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
const text=(x,y,s,size=20,color=C.text,weight=400,extra="")=>`<text x="${x}" y="${y}" font-family="Arial,Helvetica,sans-serif" font-size="${size}" font-weight="${weight}" fill="${color}" ${extra}>${esc(s)}</text>`;
const mono=(x,y,s,size=12,color=C.muted)=>text(x,y,s,size,color,500,'letter-spacing="1.5"');
const rect=(x,y,w,h,fill=C.panel,rx=12,stroke=C.line)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${stroke}"/>`;
const line=(x,y,x2,y2)=>`<path d="M${x} ${y}L${x2} ${y2}" stroke="${C.line}" fill="none"/>`;
function svg(name,w,h,title,body){files[`assets/profile/${name}.svg`]=`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-labelledby="title desc">
<title id="title">${esc(title)}</title><desc id="desc">${esc(title)}. Original decorative vector artwork.</desc>
<defs><radialGradient id="glow"><stop stop-color="#2457ae" stop-opacity=".35"/><stop offset="1" stop-color="${C.bg}" stop-opacity="0"/></radialGradient><linearGradient id="accent"><stop stop-color="${C.blue}"/><stop offset="1" stop-color="${C.cyan}"/></linearGradient><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="${C.line}" stroke-opacity=".32"/></pattern><clipPath id="bounds"><rect width="${w}" height="${h}" rx="20"/></clipPath></defs>
<style>.pulse{animation:pulse 4s ease-in-out infinite}@keyframes pulse{50%{opacity:.4}}@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>
<g clip-path="url(#bounds)">${rect(0,0,w,h,C.bg,20)}${body}</g>${rect(.5,.5,w-1,h-1,"none",20)}</svg>\n`;}
function terminal(x,y,w){
return `<g transform="translate(${x} ${y})">${rect(0,0,w,222,"#101b30",14)}<circle cx="20" cy="21" r="4" fill="#fb7185"/><circle cx="35" cy="21" r="4" fill="#fbbf24"/><circle cx="50" cy="21" r="4" fill="#67e8f9"/>${mono(76,25,"developer.py",11)}${line(0,42,w,42)}${text(22,78,"class Developer:",18,C.blue,600)}${text(40,111,'name = "Zaid Mayyalleh"',16)}${text(40,141,'focus = ["Web", "Backend", "AI"]',15,C.cyan)}${text(40,181,"build · learn · improve",15,C.muted)}<path d="M22 199H42" stroke="${C.cyan}" stroke-width="3" class="pulse"/></g>`;
}
for(const mobile of [false,true]){
const w=mobile?600:1200, suffix=mobile?"-mobile":"";
let b=`<ellipse cx="${w-100}" cy="230" rx="430" ry="340" fill="url(#glow)"/><rect x="${mobile?0:720}" width="${w}" height="${mobile?690:490}" fill="url(#grid)"/>`;
b+=mono(32,40,"ZM / ZAIDMOEN",13,C.cyan)+mono(w-(mobile?143:207),40,mobile?"PALESTINE":"BASED IN PALESTINE",11)+line(32,62,w-32,62);
b+=mono(36,112,"FULL-STACK DEVELOPER",13,C.blue);
b+=text(30,mobile?184:212,"Zaid",mobile?78:108,C.text,750,'letter-spacing="-4"');
b+=text(30,mobile?258:310,"Mayyalleh.",mobile?70:94,C.text,750,'letter-spacing="-4"');
b+=text(36,mobile?304:356,"Curiosity into code.",mobile?25:30,C.cyan,500);
b+=text(36,mobile?339:393,"Web experiences. Backend systems. Applied AI.",mobile?18:21,C.muted);
b+=terminal(mobile?36:760,mobile?373:143,mobile?528:400);
b+=line(36,mobile?630:445,w-36,mobile?630:445);
b+=mono(36,mobile?664:476,"AN-NAJAH NATIONAL UNIVERSITY",mobile?11:12);
b+=mono(mobile?400:911,mobile?664:476,"ALWAYS BUILDING",11,C.cyan);
svg("hero"+suffix,w,mobile?692:500,"Zaid Mayyalleh — Full-stack developer based in Palestine",b);
const projects=[
["api","01","Books Management API","BACKEND","FastAPI / MySQL / JWT","Relational data. Clear permissions.","{ }",C.cyan],
["voxel","02","Pinch Voxel Studio","COMPUTER VISION","Python / OpenCV / MediaPipe","Build in 3D with hand gestures.","◇",C.blue],
["web","03","Palestine Now","WEB EXPERIENCE","React / Vite / Tailwind CSS","An Arabic-first interface, built in RTL.","</>","#c4b5fd"],
["ml","04","Bank Marketing ML","MACHINE LEARNING","Python / scikit-learn / Jupyter","Explore data. Compare models.","ƒ(x)","#f9a8d4"]];
for(const [kind,n,title,category,stack,desc,icon,color] of projects){
let p=`<rect width="4" height="${mobile?240:188}" fill="${color}"/>`;
p+=mono(28,35,n+" / "+category,11,color);
p+=text(28,mobile?86:87,title,mobile?32:37,C.text,700,'letter-spacing="-1"');
p+=text(28,mobile?123:123,desc,mobile?18:20,C.muted);
p+=mono(28,mobile?202:160,stack,mobile?13:12,color);
p+=rect(w-108,24,78,48,"#14223a",10)+text(w-69,57,icon,26,color,500,'text-anchor="middle"');
p+=text(w-56,mobile?207:164,"↗",26,color);
svg("project-"+kind+suffix,w,mobile?240:188,title+" — "+stack,p);
}
const rows=[["01","LANGUAGES",["Python / JavaScript / TypeScript","C++ / SQL"]],["02","WEB & BACKEND",["React / FastAPI / Django","MySQL / Supabase"]],["03","AI & WORKFLOW",["OpenCV / MediaPipe","scikit-learn / Git"]]];
b="";
rows.forEach(([n,label,tools],i)=>{
const y=mobile?36+i*126:39+i*76;
b+=mono(28,y,n,12,C.cyan)+mono(68,y,label,12,C.blue);
if(mobile){b+=text(28,y+36,tools[0],21)+text(28,y+66,tools[1],21);}else{b+=text(322,y,tools.join(" / "),22);}
if(i<2)b+=line(28,y+(mobile?87:30),w-28,y+(mobile?87:30));
});
svg("stack"+suffix,w,mobile?386:234,"Tools used across projects and ongoing learning",b);
b=`<ellipse cx="${w-50}" cy="130" rx="400" ry="220" fill="url(#glow)"/>`;
b+=mono(30,39,"LET'S BUILD SOMETHING USEFUL.",12,C.cyan);
b+=text(28,mobile?100:115,"Good ideas deserve",mobile?39:58,C.text,700,'letter-spacing="-1.5"');
b+=text(28,mobile?150:178,"great execution.",mobile?39:58,C.text,700,'letter-spacing="-1.5"');
b+=text(30,mobile?201:226,"Internships / Junior roles / Collaboration",mobile?18:20,C.muted);
b+=text(w-75,mobile?255:152,"↗",mobile?46:70,C.cyan);
svg("connect"+suffix,w,mobile?282:262,"Contact Zaid — internships, junior roles and collaboration",b);
}
return files;
}

for (const [path, content] of Object.entries(buildArtwork())) {
  const target = new URL('../' + path, import.meta.url);
  mkdirSync(fileURLToPath(new URL('.', target)), { recursive: true });
  writeFileSync(target, content);
}
