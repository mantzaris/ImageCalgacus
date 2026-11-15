#!/usr/bin/env python3
"""Render manuscript figures from bundled saved values/pixels; no model execution."""
from pathlib import Path
import hashlib
import json
import textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/'data/figure_data.json').read_text())
INP=HERE/'data/figure_inputs'
OUT=HERE/'figures'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'axes.titlesize':9,
                    'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42,'ps.fonttype':42,
                    'svg.fonttype':'none','svg.hashsalt':'imagecalgacus-icbdaia',
                    'axes.spines.top':False,'axes.spines.right':False})
COLORS=['#0072B2','#009E73','#D55E00']; MARKERS=['o','s','^']; METHODS=['fixed','gated','arithmetic']

def save(fig,stem):
    fig.savefig(OUT/(stem+'.pdf'),metadata={'Creator':'Saved-evidence presentation script','CreationDate':None})
    fig.savefig(OUT/(stem+'.svg'))
    fig.savefig(OUT/(stem+'.png'),dpi=200)
    plt.close(fig)

def picture(fig, rect, arr):
    ax=fig.add_axes(rect);ax.imshow(arr,cmap='gray',vmin=0,vmax=255,interpolation='nearest');ax.set_axis_off()

def overview():
    src=np.asarray(Image.open(INP/'source.png'));rec=np.asarray(Image.open(INP/'recovered.png'))
    assert src.shape==rec.shape==(16,16) and np.array_equal(src,rec)
    assert rec.tobytes()==(INP/'recovered.gray').read_bytes()
    msg=(INP/'source.txt').read_bytes();assert msg==(INP/'recovered.txt').read_bytes()
    carrier=(INP/'carrier.txt').read_text();excerpt=carrier.split('\n\n')[0]
    assert (INP/'carrier.txt').read_bytes().startswith(excerpt.encode())
    png=np.asarray(Image.open(INP/'carrier.png'));assert png.shape==(31,32,3)
    fig=plt.figure(figsize=(122/25.4,65/25.4))
    fig.text(.01,.956,'A  Image → saved text → recovered image',fontsize=9,weight='bold')
    for x, arr, label in [(.02,src,'Source'),(.81,rec,'Recovered')]:
        fig.text(x+.08,.862,label,ha='center',fontsize=8)
        picture(fig,[x,.56,.16,.29],arr)
        fig.text(x+.08,.50,'16 × 16 pixels',ha='center',fontsize=8)
    fig.text(.225,.862,'Delivered text (verbatim excerpt)',fontsize=8)
    wrapped=textwrap.fill(excerpt,width=46,replace_whitespace=False,drop_whitespace=False)
    fig.text(.225,.808,wrapped,fontsize=8,va='top',linespacing=1.18)
    fig.text(.225,.535,'Full carrier: 616 tokens; 2,827 UTF-8 bytes',fontsize=8)
    fig.text(.01,.425,'B  Message → saved PNG → recovered message',fontsize=9,weight='bold')
    for x,label in [(.02,'Source text'),(.70,'Recovered text')]:
        fig.text(x,.337,label,fontsize=8)
        fig.text(x,.282,textwrap.fill(msg.decode(),width=23),fontsize=8,va='top',linespacing=1.18)
    picture(fig,[.385,.06,.21,.27],png)
    fig.text(.49,.02,'32 × 31 RGB',fontsize=8,ha='center')
    save(fig,'overview')

def recovery():
    fig,axes=plt.subplots(1,2,figsize=(122/25.4,42/25.4))
    fig.subplots_adjust(left=.15,right=.97,bottom=.29,top=.77,wspace=.36)
    for k,(ax,direction) in enumerate(zip(axes,['image-to-text','text-to-image'])):
        for i,m in enumerate(METHODS):
            row=next(c for c in DATA['recovery_cells'] if c['direction']==direction and c['method']==m)
            value=row['rate']['mean'];lo,hi=row['rate']['grouped_95_interval']; y=2-i
            ax.errorbar(value,y,xerr=[[value-lo],[hi-value]],fmt=MARKERS[i],color=COLORS[i],capsize=2,markersize=4)
            ax.annotate(f"{row['exact_recovery_count']}/{row['n_attempted']}",(value,y),xytext=(-5,5) if value else (6,2),textcoords='offset points',fontsize=8,ha='right' if value else 'left')
        ax.set_yticks([2,1,0]);ax.set_yticklabels(['Fixed','Gated','A1'] if k==0 else ['', '', ''])
        ax.set_ylim(-.45,2.55);ax.grid(axis='x',color='#dddddd',linewidth=.5);ax.set_axisbelow(True)
        ax.set_xlim(-.15,3.8) if k==0 else ax.set_xlim(-.012,.31)
        ax.set_xticks([0,1,2,3] if k==0 else [0,.1,.2,.3])
        ax.set_xlabel('Useful bits/token' if k==0 else 'Useful bits/channel')
        ax.set_title('A  Text carriers' if k==0 else 'B  PNG carriers',loc='left',fontweight='bold',pad=9)
    save(fig,'recovery_rate')

def context():
    fig,axes=plt.subplots(1,2,figsize=(122/25.4,47/25.4),gridspec_kw={'width_ratios':[1.6,1]})
    fig.subplots_adjust(left=.15,right=.98,bottom=.35,top=.8,wspace=.36)
    for j,m in enumerate(METHODS):
        c=next(c for c in DATA['context_cells'] if c['method']==m and c['score']=='surprisal_bits_mean');y=2-j
        for prefix,dy,color,marker in [('correct',.12,COLORS[0],'o'),('mismatch',-.12,COLORS[2],'D')]:
            val=c[prefix+'_auc'];lo,hi=c[prefix+'_95_interval']
            axes[0].errorbar(val,y+dy,xerr=[[val-lo],[hi-val]],color=color,fmt=marker,capsize=2,markersize=4,label={'correct':'Correct row','mismatch':'Mismatched row'}[prefix] if j==0 else None)
        val=c['difference'];lo,hi=c['difference_95_interval']
        axes[1].errorbar(val,y,xerr=[[val-lo],[hi-val]],color='#333333',fmt='s',capsize=2,markersize=4)
    for ax in axes:
        ax.set_ylim(-.45,2.55);ax.grid(axis='x',color='#eeeeee',linewidth=.5);ax.set_axisbelow(True)
    axes[0].set_yticks([2,1,0]);axes[0].set_yticklabels(['Fixed','Gated','A1']);axes[1].set_yticks([2,1,0]);axes[1].set_yticklabels(['','',''])
    axes[0].set_xlim(0,1);axes[0].set_xticks([0,.5,1]);axes[0].axvline(.5,color='#999999',ls=':',lw=.8)
    axes[1].set_xlim(-.3,.15);axes[1].set_xticks([-.2,0,.1]);axes[1].axvline(0,color='#999999',ls=':',lw=.8)
    axes[0].set_xlabel('Surprisal AUC');axes[1].set_xlabel('AUC change')
    axes[0].set_title('A  Observer context',loc='left',fontweight='bold',pad=8)
    axes[1].set_title('B  Paired change',loc='left',fontweight='bold',pad=8)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.55,.005),ncol=2,frameon=False,fontsize=8,handletextpad=.5,columnspacing=1)
    save(fig,'context_auc')

if __name__=='__main__':
    for src,record in DATA['inputs'].items():
        if 'local' in record:
            assert hashlib.sha256((HERE/record['local']).read_bytes()).hexdigest()==record['sha256'],src
    overview();recovery();context()
    outputs={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*')) if p.suffix in ('.pdf','.svg','.png')}
    (HERE/'data/figure_rendering.json').write_text(json.dumps({'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'output_hashes':outputs,'new_experiments':False,'matplotlib':matplotlib.__version__,'numpy':np.__version__,'Pillow':Image.__version__},indent=2)+'\n')
    print('Rendered three figures from bundled saved evidence.')
