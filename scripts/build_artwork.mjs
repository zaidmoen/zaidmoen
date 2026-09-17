// Generate the profile artwork with Node.js 18+. No dependencies.
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

function buildArtwork() {
  const files = {};
  const C = { ink: "#141414", panel: "#1c1c1c", paper: "#f2efe8", muted: "#aaa69e", line: "#363431", orange: "#ff794b" };
  const escape = value => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
  const t = (x,y,value,size=20,color=C.paper,weight=400,extra="") => `<text x="${x}" y="${y}" font-family="Arial,Helvetica,sans-serif" font-size="${size}" font-weight="${weight}" fill="${color}" ${extra}>${escape(value)}</text>`;
  const label = (x,y,value,color=C.muted,size=12) => t(x,y,value,size,color,500,'letter-spacing="1.7"');
  const box = (x,y,w,h,fill=C.panel,r=12,stroke="none") => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" stroke="${stroke}"/>`;
  const path = (d,color=C.line,width=1,extra="") => `<path d="${d}" stroke="${color}" stroke-width="${width}" fill="none" ${extra}/>`;
  const dot = (x,y,r,color=C.orange) => `<circle cx="${x}" cy="${y}" r="${r}" fill="${color}"/>`;
  const pill = (x,y,value,width) => box(x,y,width,30,"#242321",15,C.line)+t(x+14,y+20,value,12,C.paper);
  function save(name,w,h,title,body,description=title) {
    files[`assets/profile/${name}.svg`] = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-labelledby="title desc">
<title id="title">${escape(title)}</title><desc id="desc">${escape(description)}</desc>
<defs><clipPath id="bounds"><rect width="${w}" height="${h}" rx="18"/></clipPath><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#44413c"/></pattern><linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fffdf7"/><stop offset=".48" stop-color="#96918b"/><stop offset="1" stop-color="#e9e4da"/></linearGradient></defs>
<style>.float{animation:float 8s ease-in-out infinite}.pulse{animation:pulse 5s ease-in-out infinite}@keyframes float{50%{transform:translateY(-6px)}}@keyframes pulse{50%{opacity:.35}}@media(prefers-reduced-motion:reduce){*{animation:none!important}}</style>
<g clip-path="url(#bounds)">${box(0,0,w,h,C.ink,18)}${body}</g>${box(.5,.5,w-1,h-1,"none",18,C.line)}</svg>\n`;
  }
  // Project a twisted ribbon and sort its faces by depth for a metallic sculpture.
  function sculpture(cx,cy,scale=1) {
    const point = (u,v) => {
      const radius=139+v*Math.cos(u/2), x=radius*Math.cos(u), y=radius*Math.sin(u), z=v*Math.sin(u/2);
      return [x*.87+z*.49, y*.66-z*.66-x*.18, y*.5+z*.75];
    };
    const faces=[];
    const steps=96, strips=10;
    for(let i=0;i<steps;i++) for(let j=0;j<strips;j++) {
      const u=i*Math.PI*2/steps, du=Math.PI*2/steps, v=-48+j*96/strips, dv=96/strips;
      const points=[point(u,v),point(u+du,v),point(u+du,v+dv),point(u,v+dv)];
      const light=Math.max(0,Math.min(1,.5+.35*Math.sin(u*2-.7)+.16*j/strips));
      const rgb=[Math.round(85+168*light),Math.round(82+166*light),Math.round(78+159*light)];
      const color=j===0||j===strips-1?C.orange:`rgb(${rgb.join(",")})`;
      faces.push({depth:points.reduce((s,p)=>s+p[2],0)/4,svg:`<path d="M${points.map(p=>`${p[0].toFixed(2)} ${p[1].toFixed(2)}`).join("L")}Z" fill="${color}" stroke="${color}" stroke-width=".5"/>`});
    }
    faces.sort((a,b)=>a.depth-b.depth);
    return `<g transform="translate(${cx} ${cy}) scale(${scale})"><ellipse cy="162" rx="125" ry="11" fill="#0b0b0b"/><circle r="215" fill="none" stroke="${C.line}"/><circle r="188" fill="none" stroke="${C.line}" stroke-dasharray="2 10"/>${path("M-236 0H-215M215 0H236M0-236V-215M0 215V236","#747068")}${dot(215,0,4)}<g class="float">${faces.map(f=>f.svg).join("")}</g>${label(-50,232,"BUILD / REFINE",C.muted,10)}</g>`;
  }
  function cube(x,y,s=35) {
    return `<g transform="translate(${x} ${y})"><path d="M0 ${-s}L${s} ${-s/2} 0 0 ${-s} ${-s/2}Z" fill="#fff2df"/><path d="M${-s} ${-s/2}L0 0V${s}L${-s} ${s/2}Z" fill="#d04c2b"/><path d="M0 0L${s} ${-s/2}V${s/2}L0 ${s}Z" fill="#ff976c"/></g>`;
  }
  // Decorative miniatures explain each project's domain without inventing product data.
  function illustration(kind) {
    let b=box(0,0,440,248,"#e9e5dc",14);
    if(kind==="api") {
      b+=label(22,28,"REQUEST → DATA", "#66615a",10);
      for(const [x,y,name] of [[28,69,"API"],[171,69,"AUTH"],[314,69,"SQL"]]) {
        b+=box(x,y,98,72,"#f8f5ef",10,"#c6bfb3")+t(x+49,y+43,name,18,C.ink,700,'text-anchor="middle"');
      }
      b+=path("M126 105H171M269 105H314","#8d8375",2);
      b+=path("M77 143V177H363V143","#8d8375",1.5);
      b+=dot(149,177,5,C.orange)+box(103,194,234,28,"#ddd6ca",6)+t(220,213,"MODELS · PERMISSIONS · MIGRATIONS",9,"#534b41",500,'text-anchor="middle"');
    } else if(kind==="voxel") {
      b=box(0,0,440,248,"#b74428",14);
      for(let i=0;i<7;i++) {
        b+=path(`M${62+i*29} ${104+i*14.5}L${222+i*29} ${24+i*14.5}`,"#cf6345");
        b+=path(`M${62+i*29} ${104-i*14.5}L${222+i*29} ${184-i*14.5}`,"#cf6345");
      }
      b+=cube(195,142,36)+cube(267,142,36)+cube(231,124,36);
      b+=`<g class="float">${cube(195,70,36)}</g>`;
      b+=path("M114 67H94V87M302 172H322V152","#ffe6d2",2);
      b+=label(22,226,"HAND TRACKING / 3D CANVAS","#ffe6d2",10);
    } else if(kind==="web") {
      b+=box(44,27,352,193,"#faf8f2",10,"#bdb5a8")+path("M44 54H396","#d8d0c5");
      b+=dot(59,41,3,"#9a9489")+dot(71,41,3,"#c4b9a7")+dot(83,41,3,C.orange);
      b+=box(286,69,91,10,C.ink,3)+box(223,89,154,5,"#a39b8c",2)+box(269,101,108,5,"#bcb4a5",2);
      b+=box(64,120,312,23,"#ebe5d9",5);
      for(let i=0;i<3;i++){
        const x=64+i*108;
        b+=box(x,154,95,48,i===2?"#cf6948":"#d3cabb",5);
        b+=path(`M${x+9} 191L${x+30} 173 ${x+43} 184 ${x+66} 162 ${x+84} 187`,i===2?"#fce7d6":"#a09686",2);
      }
    } else {
      b=box(0,0,440,248,"#262522",14);
      const layers=[[62,[74,124,174]],[168,[52,100,148,196]],[274,[76,124,172]],[377,[100,148]]];
      layers.forEach(([x,ys],i)=>{
        if(i<layers.length-1)for(const y of ys)for(const ny of layers[i+1][1]) b+=path(`M${x} ${y}L${layers[i+1][0]} ${ny}`,"#51483e");
      });
      b+=path("M62 124L168 100 274 124 377 100",C.orange,2);
      layers.forEach(([x,ys],i)=>ys.forEach(y=>{b+=dot(x,y,8,"#262522")+`<circle cx="${x}" cy="${y}" r="7" fill="none" stroke="${i===3?C.orange:"#b8a68b"}" stroke-width="2"/>`;}));
      b+=label(22,27,"PATTERNS → PREDICTIONS",C.muted,10);
      b+=label(22,230,"PREPROCESS / COMPARE / EVALUATE",C.muted,10);
    }
    return b;
  }
  const projects=[
    ["api","01","Books Management API","BACKEND ENGINEERING","FastAPI / MySQL / JWT","Relational data. Deliberate design."],
    ["voxel","02","Pinch Voxel Studio","COMPUTER VISION","Python / OpenCV / MediaPipe","Your hands become the interface."],
    ["web","03","Palestine Now","WEB DEVELOPMENT","React / Vite / Tailwind CSS","Local discovery. An Arabic-first experience."],
    ["ml","04","Bank Marketing ML","APPLIED MACHINE LEARNING","Python / scikit-learn / Jupyter","Finding useful patterns in the data."]
  ];
  for(const mobile of [false,true]) {
    const w=mobile?600:1200,suffix=mobile?"-mobile":"";
    let b=label(36,41,"ZM / ZAID MAYYALLEH",C.paper,12)+label(w-(mobile?132:210),41,mobile?"PALESTINE":"DEVELOPER PORTFOLIO",C.muted,10);
    b+=path(`M36 64H${w-36}`);
    b+=label(40,117,"FULL-STACK / BACKEND / APPLIED AI",C.orange,mobile?11:12);
    b+=t(32,mobile?218:255,"Zaid",mobile?115:151,C.paper,750,'letter-spacing="-7"');
    b+=t(34,mobile?292:351,"Mayyalleh.",mobile?77:96,C.paper,750,'letter-spacing="-5"');
    b+=t(40,mobile?337:408,"Built on curiosity.",mobile?27:32,C.paper,400);
    b+=t(40,mobile?370:446,"Refined through code.",mobile?27:32,C.muted,400);
    b+=sculpture(mobile?300:929,mobile?600:302,mobile?.79:1.06);
    b+=pill(40,mobile?821:505,"BUILD",80)+pill(130,mobile?821:505,"LEARN",83)+pill(223,mobile?821:505,"ITERATE",96);
    b+=path(`M36 ${mobile?878:574}H${w-36}`);
    b+=label(40,mobile?909:607,"AN-NAJAH NATIONAL UNIVERSITY",C.muted,10);
    b+=dot(w-188,mobile?905:603,3,C.orange)+label(w-176,mobile?909:607,"ALWAYS BUILDING",C.paper,10);
    save("hero"+suffix,w,mobile?935:630,"Zaid Mayyalleh — Full-stack developer in Palestine",b,"Built on curiosity. Refined through code. Full-stack development, backend systems, and applied AI. A metallic twisted ribbon accompanies the developer's name; subtle motion respects reduced-motion preferences.");
    for(const [kind,n,title,category,stack,desc] of projects) {
      b=label(32,40,n+" / "+category,C.orange,11);
      if(mobile) {
        b+=`<g transform="translate(32 66) scale(1.21818)">${illustration(kind)}</g>`;
        b+=t(30,417,title,35,C.paper,700,'letter-spacing="-1.1"');
        b+=t(32,453,desc,21,C.muted);
        b+=path("M32 480H568");
        b+=t(32,514,stack,17,C.paper)+t(540,519,"↗",28,C.orange);
      } else {
        b+=t(30,110,title,43,C.paper,700,'letter-spacing="-1.5"');
        b+=t(32,156,desc,22,C.muted);
        b+=t(32,230,stack,17,C.paper);
        b+=label(32,285,"EXPLORE REPOSITORY",C.muted,10)+t(218,288,"↗",19,C.orange);
        b+=`<g transform="translate(726 32)">${illustration(kind)}</g>`;
      }
      save("project-"+kind+suffix,w,mobile?545:314,title+" — "+stack,b,desc+" Decorative project illustration, not a product screenshot.");
    }
    const groups=[
      ["01","Languages",["Python · JavaScript · TypeScript","C++ · SQL"]],
      ["02","Web & backend",["React · FastAPI · Django","MySQL · Supabase"]],
      ["03","AI & workflow",["OpenCV · MediaPipe","scikit-learn · Git"]]
    ];
    b="";
    groups.forEach(([n,title,tools],i)=>{
      const x=mobile?28:28+i*389,y=mobile?28+i*166:28;
      b+=box(x,y,mobile?544:366,145,C.panel,10,C.line);
      b+=label(x+20,y+28,n,C.orange,11);
      b+=t(x+56,y+29,title,20,C.paper,600);
      b+=t(x+20,y+81,tools[0],mobile?22:18,C.muted);
      b+=t(x+20,y+113,tools[1],mobile?22:18,C.muted);
    });
    save("stack"+suffix,w,mobile?526:201,"Tools across projects and ongoing learning",b,"Python, JavaScript, TypeScript, C++, SQL, React, FastAPI, Django, MySQL, Supabase, OpenCV, MediaPipe, scikit-learn, and Git. Tools used and explored, not proficiency ratings.");
    b=box(0,0,w,mobile?329:294,C.paper,18)+label(32,39,"NEXT / LET'S CONNECT","#615b52",11);
    b+=t(28,mobile?112:134,"Have an idea?",mobile?59:86,C.ink,700,'letter-spacing="-3"');
    b+=t(30,mobile?175:215,"Let's build it.",mobile?59:86,C.ink,700,'letter-spacing="-3"');
    b+=t(32,mobile?232:262,"Internships · Junior roles · Collaboration",mobile?19:20,"#615b52");
    b+=box(w-90,mobile?249:101,58,58,C.orange,29)+t(w-61,mobile?290:143,"↗",38,C.ink,400,'text-anchor="middle"');
    save("connect"+suffix,w,mobile?329:294,"Let's connect — contact Zaid",b,"Open to internships, junior roles, and collaboration. Email Zaid Mayyalleh.");
  }
  return files;
}

for (const [path, content] of Object.entries(buildArtwork())) {
  const target = new URL('../' + path, import.meta.url);
  mkdirSync(fileURLToPath(new URL('.', target)), { recursive: true });
  writeFileSync(target, content);
}
