import React from 'react';
const categories=[['Best Apps','The tools that make a difference.','#ff8464'],['Best Games','The experiences we keep coming back to.','#f5cc45'],['Bug Fixes','The fixes that make everything better.','#8ed5bf'],['Best Memes','The laughs we will remember.','#c9bbef']];
function Podium({id}){return <svg className="hk-reward-stage" viewBox="0 0 460 250" role="img" aria-label="Three mystery winners. Second place left, first place center, third place right.">
 <defs><linearGradient id={`stone-${id}`} x2="0" y2="1"><stop stopColor="#d1d4d9"/><stop offset="1" stopColor="#ecece9"/></linearGradient><linearGradient id={`pal-${id}`} x2="1" y2="1"><stop stopColor="#afb4bf"/><stop offset="1" stopColor="#7b8493"/></linearGradient><linearGradient id={`mist-${id}`} x2="0" y2="1"><stop stopColor="#faf9f5" stopOpacity="0"/><stop offset=".7" stopColor="#faf9f5" stopOpacity=".78"/><stop offset="1" stopColor="#faf9f5"/></linearGradient></defs>
 <ellipse cx="230" cy="223" rx="179" ry="15" fill="#b8bbc3" opacity=".13"/>
 {[[2,121,139],[1,230,108],[3,339,158]].map(([rank,x,y])=><g key={rank}>
 <path d={`M${x-48} ${y+9}L${x} ${y-2}L${x+48} ${y+9}V220H${x-48}Z`} fill={`url(#stone-${id})`} stroke="#c2c6cf"/>
 <path d={`M${x-48} ${y+9}L${x} ${y+21}L${x+48} ${y+9}M${x} ${y+21}V220`} fill="none" stroke="#b9bec8" opacity=".8"/>
 <text x={x} y={y+54} textAnchor="middle" fontSize="20" fontWeight="700" fill="#939ba9">0{rank}</text>
 <ellipse className="hk-reward-shadow" cx={x} cy={y+9} rx="26" ry="5" fill="#687384" opacity=".13"/>
 <g transform={`translate(${x} ${y-47})`}><g className={`hk-reward-pal hk-reward-pal-${rank}`}>
 <path d="M-27 10C-40 20-42 5-31-4L-29-17C-26-35-9-40 0-38C18-40 29-29 30-13L32-3C46 6 37 20 27 11L24 23C21 32 10 27 6 24C2 29-4 29-9 24C-16 31-25 28-26 21Z" fill={`url(#pal-${id})`}/>
 <path d="M-21-17C-18-28-8-31-2-30" fill="none" stroke="#dce0e6" strokeWidth="3" strokeLinecap="round" opacity=".55"/>
 <text x="0" y="12" textAnchor="middle" fill="white" fontSize="38" fontWeight="700">?</text></g></g></g>)}
 <path d="M37 194Q116 159 206 190T424 185V246H37Z" fill={`url(#mist-${id})`}/>
 <path d="M40 220Q113 195 201 216T423 207" fill="none" stroke="#fff" strokeWidth="11" opacity=".4"/>
 </svg>}
export default function Rewards(){return <section className="hk-rewards" aria-labelledby="hk-rewards-title"><div className="hk-rewards-intro"><div><div className="hk-eyebrow">The finish line has a few secrets.</div><h1 id="hk-rewards-title">Rewards<em>.</em></h1><p>Four categories. Three places each.<br/>The podiums are ready. The names are still a mystery.</p></div><aside><strong>The reveal comes at the finish.</strong>Winners will be announced at the end of the competition.</aside></div><div className="hk-reward-grid">{categories.map(([name,desc,color],i)=><section className="hk-reward" key={name} style={{'--category':color}} aria-labelledby={`hk-reward-${i}`}><header><span className="hk-reward-number">0{i+1}</span><div><h2 id={`hk-reward-${i}`}>{name}</h2><p>{desc}</p></div><span className="hk-reward-top">TOP 3</span></header><div className="hk-reward-scene"><Podium id={i}/><div className="hk-reward-places" aria-hidden="true"><span>2nd place</span><span>1st place</span><span>3rd place</span></div></div><footer><span>REVEAL PENDING</span><h3>To Be Announced</h3><p>At the end of the competition.</p></footer></section>)}</div></section>}
