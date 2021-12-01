#!/usr/local/bin/python3

import os
import re
import sys


from xml.sax import handler, make_parser
from xml.sax.handler import feature_namespaces, feature_external_ges, feature_external_pes


# DV block size (PAL)
BLOCKSIZE=144000
# Images per second (PAL)
FPS=25

#
# Templates for Kdenlive/Mlt files
#

# File header
xml_header = """<?xml version='1.0' encoding='utf-8'?>
<mlt LC_NUMERIC="C" producer="main_bin" version="7.0.0" root="%(curdir)s">
 <profile frame_rate_num="25" sample_aspect_num="16" display_aspect_den="3" colorspace="601" progressive="0" description="DV/DVD PAL" display_aspect_num="4" frame_rate_den="1" width="720" height="576" sample_aspect_den="15"/>"""

# Template for a producer (source media)
producer_template = """ <producer id="%(string_id)s" in="00:00:00.000" out="%(end_timecode)s">
  <property name="length">%(size_frames)s</property>
  <property name="eof">pause</property>
  <property name="resource">%(file)s</property>
  <property name="audio_index">1</property>
  <property name="video_index">0</property>
  <property name="mute_on_pause">0</property>
  <property name="mlt_service">avformat-novalidate</property>
  <property name="seekable">1</property>
  <property name="aspect_ratio">1.06667</property>
  <property name="kdenlive:clipname"/>
  <property name="kdenlive:folderid">-1</property>
  <property name="kdenlive:id">%(id)d</property>
  <property name="kdenlive:file_size">%(size_bytes)s</property>
  <property name="kdenlive:audio_max1">1</property>
  <property name="xml">was here</property>
  <property name="meta.media.nb_streams">2</property>
  <property name="meta.media.0.stream.type">video</property>
  <property name="meta.media.0.stream.frame_rate">25</property>
  <property name="meta.media.0.stream.sample_aspect_ratio">1.06667</property>
  <property name="meta.media.0.codec.width">720</property>
  <property name="meta.media.0.codec.height">576</property>
  <property name="meta.media.0.codec.rotate">0</property>
  <property name="meta.media.0.codec.frame_rate">25</property>
  <property name="meta.media.0.codec.pix_fmt">yuv420p</property>
  <property name="meta.media.0.codec.sample_aspect_ratio">1.06667</property>
  <property name="meta.media.0.codec.colorspace">601</property>
  <property name="meta.media.0.codec.name">dvvideo</property>
  <property name="meta.media.0.codec.long_name">DV (Digital Video)</property>
  <property name="meta.media.0.codec.bit_rate">25000000</property>
  <property name="meta.media.1.stream.type">audio</property>
  <property name="meta.media.1.codec.sample_fmt">s16</property>
  <property name="meta.media.1.codec.sample_rate">48000</property>
  <property name="meta.media.1.codec.channels">2</property>
  <property name="meta.media.1.codec.name">pcm_s16le</property>
  <property name="meta.media.1.codec.long_name">PCM signed 16-bit little-endian</property>
  <property name="meta.media.1.codec.bit_rate">1536000</property>
  <property name="meta.media.sample_aspect_num">16</property>
  <property name="meta.media.sample_aspect_den">15</property>
  <property name="meta.media.frame_rate_num">25</property>
  <property name="meta.media.frame_rate_den">1</property>
  <property name="meta.media.colorspace">601</property>
  <property name="meta.media.color_trc">2</property>
  <property name="meta.media.has_b_frames">0</property>
  <property name="meta.media.width">720</property>
  <property name="meta.media.height">576</property>
  <property name="meta.media.color_range">mpeg</property>
  <property name="meta.media.top_field_first">0</property>
  <property name="meta.media.progressive">0</property>
%(more_properties)s </producer>"""

#
# Optional properties for a producer. Used to describe a timeline element.
#
more_properties_template = """  <property name="kdenlive:zone_in">%(beg)d</property>
  <property name="kdenlive:zone_out">%(end)d</property>
  <property name="set.test_audio">%(audio)d</property>
  <property name="set.test_image">%(video)d</property>"""

#
# Template for the "main_bin" playlist. It contains the list of source medias
# to choose from in the Kdenlive interface.
#
playlist_bin_template = """ <playlist id="main_bin">
  <property name="kdenlive:docproperties.activeTrack">3</property>
  <property name="kdenlive:docproperties.audioChannels">2</property>
  <property name="kdenlive:docproperties.audioTarget">1</property>
  <property name="kdenlive:docproperties.disablepreview">0</property>
  <property name="kdenlive:docproperties.enableTimelineZone">0</property>
  <property name="kdenlive:docproperties.enableexternalproxy">0</property>
  <property name="kdenlive:docproperties.enableproxy">0</property>
  <property name="kdenlive:docproperties.generateimageproxy">0</property>
  <property name="kdenlive:docproperties.generateproxy">0</property>
  <property name="kdenlive:docproperties.kdenliveversion">21.08.1</property>
  <property name="kdenlive:docproperties.position">0</property>
  <property name="kdenlive:docproperties.previewextension"/>
  <property name="kdenlive:docproperties.previewparameters"/>
  <property name="kdenlive:docproperties.profile">Makefile.bak</property>
  <property name="kdenlive:docproperties.proxyextension"/>
  <property name="kdenlive:docproperties.proxyimageminsize">2000</property>
  <property name="kdenlive:docproperties.proxyimagesize">800</property>
  <property name="kdenlive:docproperties.proxyminsize">1000</property>
  <property name="kdenlive:docproperties.proxyparams"/>
  <property name="kdenlive:docproperties.proxyresize">640</property>
  <property name="kdenlive:docproperties.scrollPos">0</property>
  <property name="kdenlive:docproperties.seekOffset">30000</property>
  <property name="kdenlive:docproperties.version">1.02</property>
  <property name="kdenlive:docproperties.verticalzoom">1</property>
  <property name="kdenlive:docproperties.videoTarget">2</property>
  <property name="kdenlive:docproperties.zonein">0</property>
  <property name="kdenlive:docproperties.zoneout">75</property>
  <property name="kdenlive:docproperties.zoom">8</property>
  <property name="kdenlive:expandedFolders"/>
  <property name="kdenlive:documentnotes"/>
  <property name="kdenlive:docproperties.groups">[
%(groups)s
]
</property>
  <property name="xml_retain">1</property>
%(entries)s </playlist>"""

#
# Entry template, one for each media (producer) present in the main bin.
#
entry_template = """  <entry producer="%(string_id)s" in="00:00:00.000" out="%(end_timecode)s"/>\n"""


#
# This is used to group corresponding audio and video tracks in Kdenlive
# (Group/Ungroup functions). One entry for each (video, audio) pair.
#
group_template = """    {
        "children": [
            {
                "data": "3:%(beg)d",
                "leaf": "clip",
                "type": "Leaf"
            },
            {
                "data": "0:%(beg)d",
                "leaf": "clip",
                "type": "Leaf"
            }
        ],
        "type": "AVSplit"
    }"""


#
# Additional black track template generated by Kdenlive in all projects, with
# a duration of 20 minutes + the timeline duration.
#
blacktrack_template = """ <producer id="black_track" in="00:00:00.000" out="%(blacktrack_end_timecode)s">
  <property name="length">2147483647</property>
  <property name="eof">continue</property>
  <property name="resource">black</property>
  <property name="aspect_ratio">1</property>
  <property name="mlt_service">color</property>
  <property name="mlt_image_format">rgb24a</property>
  <property name="set.test_audio">0</property>
 </producer>"""

#
# Template for the end of the Kdenlive XML file, describing the audio and
# video playlists and how they should be assembled.
#
tail_xml = """
%(p0_producers)s <playlist id="playlist0">
  <property name="kdenlive:audio_track">1</property>
%(playlist0)s </playlist>
 <playlist id="playlist1">
  <property name="kdenlive:audio_track">1</property>
 </playlist>
 <tractor id="tractor0" in="00:00:00.000" out="%(end_timecode)s">
  <property name="kdenlive:audio_track">1</property>
  <property name="kdenlive:trackheight">69</property>
  <property name="kdenlive:timeline_active">1</property>
  <property name="kdenlive:collapsed">0</property>
  <property name="kdenlive:thumbs_format"/>
  <property name="kdenlive:audio_rec"/>
  <track hide="video" producer="playlist0"/>
  <track hide="video" producer="playlist1"/>
  <filter id="filter0">
   <property name="channel">-1</property>
   <property name="mlt_service">panner</property>
   <property name="internal_added">237</property>
   <property name="start">0.5</property>
   <property name="disable">1</property>
  </filter>
 </tractor>
 <playlist id="playlist2">
  <property name="kdenlive:audio_track">1</property>
 </playlist>
 <playlist id="playlist3">
  <property name="kdenlive:audio_track">1</property>
 </playlist>
 <tractor id="tractor1" in="00:00:00.000">
  <property name="kdenlive:audio_track">1</property>
  <property name="kdenlive:trackheight">69</property>
  <property name="kdenlive:timeline_active">1</property>
  <property name="kdenlive:collapsed">0</property>
  <property name="kdenlive:thumbs_format"/>
  <property name="kdenlive:audio_rec"/>
  <track hide="video" producer="playlist2"/>
  <track hide="video" producer="playlist3"/>
  <filter id="filter1">
   <property name="channel">-1</property>
   <property name="mlt_service">panner</property>
   <property name="internal_added">237</property>
   <property name="start">0.5</property>
   <property name="disable">1</property>
  </filter>
 </tractor>
 <playlist id="playlist4"/>
 <playlist id="playlist5"/>
 <tractor id="tractor2" in="00:00:00.000">
  <property name="kdenlive:trackheight">69</property>
  <property name="kdenlive:timeline_active">1</property>
  <property name="kdenlive:collapsed">0</property>
  <property name="kdenlive:thumbs_format"/>
  <property name="kdenlive:audio_rec"/>
  <track hide="audio" producer="playlist4"/>
  <track hide="audio" producer="playlist5"/>
 </tractor>
%(p6_producers)s <playlist id="playlist6">
  %(playlist6)s
 </playlist>
 <playlist id="playlist7"/>
 <tractor id="tractor3" in="00:00:00.000" out="%(end_timecode)s">
  <property name="kdenlive:trackheight">69</property>
  <property name="kdenlive:timeline_active">1</property>
  <property name="kdenlive:collapsed">0</property>
  <property name="kdenlive:thumbs_format"/>
  <property name="kdenlive:audio_rec"/>
  <track hide="audio" producer="playlist6"/>
  <track hide="audio" producer="playlist7"/>
 </tractor>
 <tractor id="tractor4" in="00:00:00.000" out="%(blacktrack_end_timecode)s">
  <track producer="black_track"/>
  <track producer="tractor0"/>
  <track producer="tractor1"/>
  <track producer="tractor2"/>
  <track producer="tractor3"/>
  <transition id="transition0">
   <property name="a_track">0</property>
   <property name="b_track">1</property>
   <property name="mlt_service">mix</property>
   <property name="kdenlive_id">mix</property>
   <property name="internal_added">237</property>
   <property name="always_active">1</property>
   <property name="accepts_blanks">1</property>
   <property name="sum">1</property>
  </transition>
  <transition id="transition1">
   <property name="a_track">0</property>
   <property name="b_track">2</property>
   <property name="mlt_service">mix</property>
   <property name="kdenlive_id">mix</property>
   <property name="internal_added">237</property>
   <property name="always_active">1</property>
   <property name="accepts_blanks">1</property>
   <property name="sum">1</property>
  </transition>
  <transition id="transition2">
   <property name="a_track">0</property>
   <property name="b_track">3</property>
   <property name="compositing">0</property>
   <property name="distort">0</property>
   <property name="rotate_center">0</property>
   <property name="mlt_service">qtblend</property>
   <property name="kdenlive_id">qtblend</property>
   <property name="internal_added">237</property>
   <property name="always_active">1</property>
  </transition>
  <transition id="transition3">
   <property name="a_track">0</property>
   <property name="b_track">4</property>
   <property name="compositing">0</property>
   <property name="distort">0</property>
   <property name="rotate_center">0</property>
   <property name="mlt_service">qtblend</property>
   <property name="kdenlive_id">qtblend</property>
   <property name="internal_added">237</property>
   <property name="always_active">1</property>
  </transition>
  <filter id="filter2">
   <property name="channel">-1</property>
   <property name="mlt_service">panner</property>
   <property name="internal_added">237</property>
   <property name="start">0.5</property>
   <property name="disable">1</property>
  </filter>
 </tractor>"""


class KinoHandler(handler.ContentHandler):
  """Kino file reader."""
  def __init__(self):
    self.stack = []
    self.all_whitespace = re.compile("^\s*$")
    self.re_frame = re.compile('^(\d+)$')
    self.re_timecode = re.compile('^(\d+):(\d\d):(\d\d)\.(\d\d\d)$')
    self.nameset = set()
    self.frame = 0
    self.cutlist = []
    self.groups = []

  def extract_frame(self, text):
    """Extract frame number or timecode from text."""
    frame = None
    n = self.re_frame.match(text)
    if n:
      frame = int(n.groups()[0])
    else:
      n = self.re_timecode.match(text)
      if n:
        h, m, s, ss = n.groups()
        frame = timecode_to_frame(h, m, s, ss)
    return frame

  def process_video(self, attr):
    """Process <video> tag."""
    file = attr['src']
    beg = self.extract_frame(attr['clipBegin'])
    end = self.extract_frame(attr['clipEnd'])

    bfile = os.path.basename(file)
    if os.path.isfile(bfile):
      file = bfile

    self.cutlist.append((file, beg, end))
    print(frame_to_timecode(self.frame), file, beg, end)
    self.groups.append(group_template % {'beg': self.frame})
    self.frame += (int(end)+1-int(beg))

    self.nameset.add(file)

  def startElement(self, name, attr):
    if name == "smil":
      assert self.stack == []
    elif name == "body":
      assert self.stack == ['smil']
    elif name == "seq":
      assert self.stack == ['smil'] or self.stack == ['smil', 'body']
    else:
      assert name == "video"
      assert self.stack == ['smil', 'seq'] or self.stack == ['smil', 'body', 'seq']
      self.process_video(attr)

    self.stack.append(name)

  def characters(self, ch):
    if not self.all_whitespace.match(ch):
      print("Skipping unexpected characters in SMIL input:", ch)

  def endElement(self, name):
    assert name == self.stack[-1]
    self.stack.pop()



def timecode_to_frame(h, m, s, ss):
  """Convert a timecode to a frame number."""
  return int(ss)//(1000//FPS) + FPS*(int(s)+int(m)*60+int(h)*3600)

def frame_to_timecode(frame):
  """Convert a frame number to a timecode."""
  seconds = frame/FPS
  h = seconds // 3600
  m = (seconds // 60) % 60
  s = seconds % 60
  return "%02d:%02d:%02d.%03d" % (h, m, s, (frame % FPS)*(1000//FPS))

def emit_kdenlive(frames, groups, nameset, cutlist, outkde):
  """Write Kdenlive XML file."""
  end_timecode = frame_to_timecode(frames)
  blacktrack_end_timecode = frame_to_timecode(frames+20*60*FPS)
  groups = ',\n'.join(groups)

  producers = {file: {'size_bytes': os.stat(file).st_size, 'file': file} for file in nameset}

  # Generate producers for playlist main_bin, which is Kdenlive's
  # media bin to pick video rushes from.

  for i, file in enumerate(sorted(producers.keys())):
    producers[file]['string_id'] = 'producer%d' % i
    producers[file]['id'] = i+1
    producers[file]['more_properties'] = ''
    size_frames = producers[file]['size_bytes']//BLOCKSIZE
    producers[file]['size_frames'] = size_frames
    producers[file]['end_timecode'] = frame_to_timecode(size_frames-1)

  # Next free producer id
  next_id = len(producers)+1

  print(xml_header % {'curdir': os.getcwd()}, file=outkde)

  # Emit producer list for the main bin.
  # Keep track of entries, to be used later when emitting the playlist.
  entries = ""
  for f in sorted(producers.keys()):
    print(producer_template % producers[f], file=outkde)
    entries += entry_template % producers[f]

  # Special black track producer
  print(blacktrack_template % {'blacktrack_end_timecode': blacktrack_end_timecode},
        file=outkde)

  # Emit playlist for the main bin
  print(playlist_bin_template % {'entries': entries, 'groups': groups}, file=outkde)

  # Create audio and video track producers for the tracks themselves (playlists)
  playlist0 = ''
  playlist6 = ''
  p0_producers = ''
  p6_producers = ''

  for file, beg, end in cutlist:
    p = producers[file].copy()

    p['string_id'] = 'producer%d' % next_id
    more = {'beg': beg, 'end': end, 'audio': 0, 'video': 1}
    p['more_properties'] = more_properties_template % more
    next_id += 1
    p0_producers += producer_template % p + '\n'

    p['beg_timecode'] = frame_to_timecode(beg)
    p['end_timecode'] = frame_to_timecode(end)
    playlist0 += """  <entry producer="%(string_id)s" in="%(beg_timecode)s" out="%(end_timecode)s">
   <property name="kdenlive:id">%(id)d</property>
  </entry>\n""" % p

    p['string_id'] = 'producer%d' % next_id
    more = {'beg': beg, 'end': end, 'audio': 1, 'video': 0}
    p['more_properties'] = more_properties_template % more
    next_id += 1
    p6_producers += producer_template % p + '\n'

    playlist6 += """  <entry producer="%(string_id)s" in="%(beg_timecode)s" out="%(end_timecode)s">
   <property name="kdenlive:id">%(id)d</property>
  </entry>""" % p

  print(tail_xml % {'playlist0': playlist0, 'playlist6': playlist6,
                    'p0_producers': p0_producers, 'p6_producers': p6_producers,
                    'end_timecode': end_timecode, 'blacktrack_end_timecode': blacktrack_end_timecode},
                    file=outkde)
  print("</mlt>", file=outkde)


if len(sys.argv) != 2 or not sys.argv[1].endswith('.kino'):
  print("Usage: %s <input.kino>" % sys.argv[0], file=sys.stderr)
  sys.exit(1)

filename = sys.argv[1]

# Read .kino (SMIL) file

ch = KinoHandler()
parser = make_parser()
parser.setContentHandler(ch)
parser.setFeature(feature_namespaces, 0)
parser.setFeature(feature_external_ges, 0)
with open(filename) as f:
  parser.parse(f)

# Write .kdenlive file

basename, _ = filename.rsplit('.', 1)
outfilename = basename + '.kdenlive'

with open(outfilename, 'w+') as outkde:
  emit_kdenlive(ch.frame, ch.groups, ch.nameset, ch.cutlist, outkde)
