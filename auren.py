#!/usr/bin/env python3
"""Auren: edit theme.json, preview, then apply to an existing rEFInd installation."""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build'
HISTORY=Path('/var/lib/auren-refind/last-install')
TOOLS={'reboot':'func_reset','shutdown':'func_shutdown','firmware':'func_firmware','about':'func_about'}

def run(*args,**kw):return subprocess.run(args,check=True,**kw)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def settings():
 c=json.loads((ROOT/'theme.json').read_text())
 if not re.fullmatch(r'#[0-9a-fA-F]{6}',c['accent']):raise ValueError('Accent must be a color such as #FF7900.')
 if not 96<=c['os_icon_size']<=256:raise ValueError('OS icon size must be 96–256.')
 if not 32<=c['utility_icon_size']<=96:raise ValueError('Utility size must be 32–96.')
 if not c['utilities'] or len(set(c['utilities']))!=len(c['utilities']) or set(c['utilities'])-TOOLS.keys():raise ValueError('Choose unique utilities: reboot, shutdown, firmware, about.')
 w,h=c['resolution']
 if not 800<=w<=7680 or not 600<=h<=4320:raise ValueError('Unsupported canvas dimensions.')
 return c

def render(source,destination,accent):
 text=source.read_text();text=re.sub('#FF7900',accent,text,flags=re.I)
 with tempfile.TemporaryDirectory(prefix='auren-svg-') as d:
  svg=Path(d)/source.name;svg.write_text(text)
  run('magick','-background','none',str(svg),'-depth','8','PNG32:'+str(destination),capture_output=True)

def build():
 from PIL import Image,ImageOps
 c=settings();BUILD.mkdir(exist_ok=True);(BUILD/'icons').mkdir(exist_ok=True)
 w,h=c['resolution'];accent=c['accent']
 if c.get('render_background_svg',False):
  render(ROOT/'sources/background.svg',BUILD/'background.png',accent)
  im=Image.open(BUILD/'background.png').convert('RGBA').resize((w,h),Image.Resampling.LANCZOS);im.save(BUILD/'background.png')
 else:
  path=Path(c['background']);path=path if path.is_absolute() else ROOT/path
  image=Image.open(path).convert('RGBA')
  if image.size==(w,h):shutil.copyfile(path,BUILD/'background.png')
  else:ImageOps.fit(image,(w,h),method=Image.Resampling.LANCZOS).save(BUILD/'background.png')
 for name in ('selection_big','selection_small'):
  render(ROOT/f'sources/{name}.svg',BUILD/f'{name}.png',accent)
 shutil.copyfile(ROOT/'assets/font.png',BUILD/'font.png')
 for name in ('os_bazzite','os_win',*TOOLS.values()):
  render(ROOT/f'sources/{name}.svg',BUILD/f'icons/{name}.png',accent)
 hide='singleuser,hints,arrows,badges,safemode,hwtest'+('' if c['show_labels'] else ',label')
 theme=f'''# Auren -- generated from theme.json
resolution {w} {h}
banner themes/auren/background.png
banner_scale fillscreen
icons_dir themes/auren/icons
selection_big themes/auren/selection_big.png
selection_small themes/auren/selection_small.png
big_icon_size {c['os_icon_size']}
small_icon_size {c['utility_icon_size']}
font themes/auren/font.png
showtools {','.join(c['utilities'])}
hideui {hide}
'''
 (BUILD/'theme.conf').write_text(theme)
 preview=Image.open(BUILD/'background.png').convert('RGBA')
 big=c['os_icon_size'];small=c['utility_icon_size'];tile0=big*9//8;tile1=small*4//3
 x0=(w+8-(tile0+8)*2)//2;y0=h//2-tile0//2
 n=len(c['utilities']);x1=(w+8-(tile1+8)*n)//2;y1=y0+tile0+16
 preview.alpha_composite(Image.open(BUILD/'selection_big.png').resize((tile0,tile0),Image.Resampling.LANCZOS),(x0,y0))
 for i,name in enumerate(('os_bazzite','os_win')):
  image=Image.open(BUILD/f'icons/{name}.png').resize((big,big),Image.Resampling.LANCZOS)
  preview.alpha_composite(image,(x0+i*(tile0+8)+(tile0-big)//2,y0+(tile0-big)//2))
 for i,tool in enumerate(c['utilities']):
  image=Image.open(BUILD/f'icons/{TOOLS[tool]}.png').resize((small,small),Image.Resampling.LANCZOS)
  preview.alpha_composite(image,(x1+i*(tile1+8)+(tile1-small)//2,y1+(tile1-small)//2))
 if c['show_labels']:
  atlas=Image.open(BUILD/'font.png').convert('RGBA');white=ImageOps.invert(atlas.convert('RGB'));white.putalpha(atlas.getchannel('A'))
  cell=atlas.width//96
  for row,line in enumerate((c['preview_description'],'Automatic boot in 10 seconds')):
   start=(w-len(line)*cell)//2;y=y1+tile1+16+row*(atlas.height+4)
   for j,char in enumerate(line):
    index=ord(char)-32 if 32<=ord(char)<127 else 95
    preview.alpha_composite(white.crop((index*cell,0,(index+1)*cell,atlas.height)),(start+j*cell,y))
 preview.convert('RGB').save(ROOT/'preview.png')
 files=[p for p in BUILD.rglob('*') if p.is_file() and p.name!='manifest.json']
 manifest={str(p.relative_to(BUILD)):digest(p) for p in files}
 (BUILD/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Preview:',ROOT/'preview.png');print('Build:',BUILD)
 return c

def root_path():
 path=Path('/boot/efi/EFI/refind')
 mount=subprocess.check_output(['findmnt','-no','FSTYPE','--target','/boot/efi'],text=True).strip()
 if mount not in ('vfat','fat','msdos'):raise RuntimeError('Expected an EFI FAT partition mounted at /boot/efi.')
 if not (path/'refind.conf').is_file():raise RuntimeError('Existing rEFInd installation not found at /boot/efi/EFI/refind.')
 return path

def atomic(path,data):
 temp=path.with_name(path.name+'.auren-tmp');temp.write_bytes(data);temp.replace(path)

def fingerprint_efi():
 return {str(p):digest(p) for p in Path('/boot/efi/EFI').rglob('*') if p.is_file() and p.suffix.lower()=='.efi'}

def apply():
 if os.geteuid()!=0:raise RuntimeError('Install must be authenticated.')
 target=root_path();theme=target/'themes/auren';config=target/'refind.conf'
 manifest=json.loads((BUILD/'manifest.json').read_text())
 for name,expected in manifest.items():
  if Path(name).is_absolute() or '..' in Path(name).parts or Path(name).suffix not in ('.png','.conf'):raise RuntimeError('Invalid asset path.')
  if digest(BUILD/name)!=expected:raise RuntimeError('Build changed; regenerate the preview first.')
 original=config.read_text()
 includes=re.findall(r'^\s*include\s+(themes/\S+\.conf)\s*$',original,re.M)
 if len(includes)>1:raise RuntimeError('More than one theme include exists; review the main config before applying.')
 changed=original
 if includes:changed=changed.replace('include '+includes[0],'include themes/auren/theme.conf')
 else:changed=changed.rstrip()+'\ninclude themes/auren/theme.conf\n'
 for name in ('bazzite','win'):
  changed=re.sub(r'(?m)^(\s*icon\s+)[^\n]*os_'+name+r'\.png\s*$',r'\g<1>/EFI/refind/themes/auren/icons/os_'+name+'.png',changed)
 for token in ('loader','volume','scanfor','timeout','default_selection'):
  pattern=rf'^\s*{token}\s+.*$'
  if re.findall(pattern,original,re.M)!=re.findall(pattern,changed,re.M):raise RuntimeError('Boot behavior would change; refusing.')
 before=fingerprint_efi();order=subprocess.check_output(['efibootmgr'],text=True)
 backup=HISTORY;backup.parent.mkdir(parents=True,exist_ok=True)
 staging=Path(tempfile.mkdtemp(prefix='auren-backup-',dir=backup.parent))
 (staging/'refind.conf').write_text(original)
 if theme.exists():shutil.copytree(theme,staging/'theme')
 (staging/'state.json').write_text(json.dumps({'installed_config_sha256':hashlib.sha256(changed.encode()).hexdigest()}))
 if backup.exists():shutil.rmtree(backup)
 staging.replace(backup)
 try:
  theme.mkdir(parents=True,exist_ok=True)
  for name in manifest:
   destination=theme/name;destination.parent.mkdir(parents=True,exist_ok=True);atomic(destination,(BUILD/name).read_bytes())
  atomic(config,changed.encode());os.sync()
  for name,expected in manifest.items():
   if digest(theme/name)!=expected:raise RuntimeError('Installed asset failed verification.')
  if fingerprint_efi()!=before or subprocess.check_output(['efibootmgr'],text=True)!=order:raise RuntimeError('Unexpected boot state change.')
 except BaseException:
  atomic(config,original.encode())
  if (backup/'theme').exists():
   if theme.exists():shutil.rmtree(theme)
   shutil.copytree(backup/'theme',theme)
  os.sync();raise
 print('Auren installed. Boot entries, EFI executables and boot order preserved.')
 print('Undo this installation: python3 auren.py restore')

def restore():
 if os.geteuid()!=0:raise RuntimeError('Restore must be authenticated.')
 target=root_path();backup=HISTORY
 if not backup.exists():raise RuntimeError('No installation made by this project is available to undo.')
 state=json.loads((backup/'state.json').read_text())
 if digest(target/'refind.conf')!=state['installed_config_sha256']:raise RuntimeError('Configuration changed since installation; inspect before restoring.')
 before=fingerprint_efi();order=subprocess.check_output(['efibootmgr'],text=True)
 theme=target/'themes/auren'
 if (backup/'theme').exists():
  if theme.exists():shutil.rmtree(theme)
  shutil.copytree(backup/'theme',theme)
 atomic(target/'refind.conf',(backup/'refind.conf').read_bytes());os.sync()
 if fingerprint_efi()!=before or subprocess.check_output(['efibootmgr'],text=True)!=order:raise RuntimeError('Unexpected boot state change.')
 print('Previous theme restored. EFI executables and boot order unchanged.')

def configure(args):
 c=settings()
 if args.accent:c['accent']=args.accent
 if args.os_size is not None:c['os_icon_size']=args.os_size
 if args.utility_size is not None:c['utility_icon_size']=args.utility_size
 if args.background:c['background']=str(Path(args.background).resolve());c['render_background_svg']=False
 if args.resolution:c['resolution']=[int(n) for n in args.resolution.lower().split('x')]
 if args.labels is not None:c['show_labels']=args.labels=='on'
 old=(ROOT/'theme.json').read_bytes()
 try:(ROOT/'theme.json').write_text(json.dumps(c,indent=2)+'\n');settings()
 except BaseException:(ROOT/'theme.json').write_bytes(old);raise
 build()

def doctor():
 import importlib.util
 missing=[name for name in ('magick','pkexec','findmnt','efibootmgr') if not shutil.which(name)]
 if importlib.util.find_spec('PIL') is None:missing.append('Python Pillow')
 print('Dependencies:',', '.join(missing)+' missing' if missing else 'ready')
 print('Settings:',ROOT/'theme.json')
 if missing:raise RuntimeError('Install the missing dependencies with your Linux distribution package manager.')
 settings();print('Settings valid.')

def status():
 guard=Path('/etc/refind/integrity-guard.py')
 if guard.is_file():run('/usr/bin/python3',str(guard),'status')
 else:print('Optional Auren integrity guard is not installed.')
 print('This project never replaces a bootloader or changes Secure Boot.')

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('command',nargs='?',choices=['build','preview','customize','install','restore','status','doctor','_apply','_restore'])
 parser.add_argument('--accent');parser.add_argument('--os-size',type=int);parser.add_argument('--utility-size',type=int)
 parser.add_argument('--background');parser.add_argument('--resolution',help='For example 1920x1080')
 parser.add_argument('--labels',choices=['on','off'])
 args=parser.parse_args()
 if not args.command:
  print('Auren rEFInd Theme\n1. Preview\n2. Customize\n3. Install theme\n4. Undo last install\n5. Status\n6. Check requirements\n0. Exit')
  choice=input('Choose: ').strip()
  args.command={'1':'preview','2':'customize','3':'install','4':'restore','5':'status','6':'doctor'}.get(choice)
  if not args.command:return
  if args.command=='customize':
   c=settings();args.accent=input(f"Accent [{c['accent']}]: ").strip() or None
   size=input(f"OS icon size [{c['os_icon_size']}]: ").strip();args.os_size=int(size) if size else None
 if args.command in ('build','preview'):build()
 if args.command=='preview':run('xdg-open',str(ROOT/'preview.png'))
 elif args.command=='customize':configure(args)
 elif args.command=='doctor':doctor()
 elif args.command=='status':status()
 elif args.command=='install':build();run('pkexec','/usr/bin/python3',str(Path(__file__)),'_apply')
 elif args.command=='restore':run('pkexec','/usr/bin/python3',str(Path(__file__)),'_restore')
 elif args.command=='_apply':apply()
 elif args.command=='_restore':restore()

if __name__=='__main__':
 try:main()
 except (ValueError,RuntimeError,OSError,subprocess.SubprocessError,KeyError) as error:sys.exit('Auren: '+str(error))
