"""
PowerPoint (.pptx) generation using Python standard library only.
Creates valid OOXML presentation files using zipfile and xml.etree.ElementTree.
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
import datetime


def create_pptx(output_path: str, data: Any) -> bool:
    """
    Generate a valid PowerPoint .pptx file from repository analysis data.
    
    Args:
        output_path: Path where the .pptx file should be created
        data: ReportData object containing analysis results
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the PPTX structure
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as pptx:
            # Add required files for a valid PPTX
            _add_content_types(pptx)
            _add_rels(pptx)
            _add_presentation(pptx)
            _add_presentation_rels(pptx)
            _add_slide_master(pptx)
            _add_slide_layout(pptx)
            _add_theme(pptx)
            
            # Add content slides based on analysis data
            _add_title_slide(pptx, data)
            _add_overview_slide(pptx, data)
            _add_statistics_slide(pptx, data)
            _add_architecture_slide(pptx, data)
            _add_quality_slide(pptx, data)
            _add_security_slide(pptx, data)
            _add_recommendations_slide(pptx, data)
            _add_summary_slide(pptx, data)
            
        return True
    except Exception as e:
        print(f"Error generating PowerPoint: {e}")
        return False


def _add_content_types(pptx: zipfile.ZipFile):
    """Add [Content_Types].xml to the package."""
    xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide3.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide4.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide5.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide6.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide7.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slides/slide8.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>'''
    pptx.writestr('[Content_Types].xml', xml_content)


def _add_rels(pptx: zipfile.ZipFile):
    """Add _rels/.rels to the package."""
    xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''
    pptx.writestr('_rels/.rels', xml_content)


def _add_presentation(pptx: zipfile.ZipFile):
    """Add ppt/presentation.xml."""
    xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" 
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" 
                saveSubsetFonts="1">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
    <p:sldId id="256" r:id="rId2"/>
    <p:sldId id="257" r:id="rId3"/>
    <p:sldId id="258" r:id="rId4"/>
    <p:sldId id="259" r:id="rId5"/>
    <p:sldId id="260" r:id="rId6"/>
    <p:sldId id="261" r:id="rId7"/>
    <p:sldId id="262" r:id="rId8"/>
    <p:sldId id="263" r:id="rId9"/>
  </p:sldIdLst>
  <p:sldSz cx="9144000" cy="6858000"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>'''
    pptx.writestr('ppt/presentation.xml', xml_content)


def _add_presentation_rels(pptx: zipfile.ZipFile):
    """Add ppt/_rels/presentation.xml.rels."""
    xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide3.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide4.xml"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide5.xml"/>
  <Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide6.xml"/>
  <Relationship Id="rId8" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide7.xml"/>
  <Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide8.xml"/>
</Relationships>'''
    pptx.writestr('ppt/_rels/presentation.xml.rels', xml_content)


def _add_slide_master(pptx: zipfile.ZipFile):
    """Add ppt/slideMasters/slideMaster1.xml."""
    xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" 
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr/>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
</p:sldMaster>'''
    pptx.writestr('ppt/slideMasters/slideMaster1.xml', xml_content)
    
    # Add relationship file for slide master
    rels_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>'''
    pptx.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', rels_content)


def _add_slide_layout(pptx: zipfile.ZipFile):
    """Add ppt/slideLayouts/slideLayout1.xml."""
    xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" 
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" 
             type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr/>
    </p:spTree>
  </p:cSld>
</p:sldLayout>'''
    pptx.writestr('ppt/slideLayouts/slideLayout1.xml', xml_content)
    
    # Add relationship file for slide layout
    rels_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>'''
    pptx.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', rels_content)


def _add_theme(pptx: zipfile.ZipFile):
    """Add ppt/theme/theme1.xml."""
    xml_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F497D"/></a:dk2>
      <a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
      <a:accent1><a:srgbClr val="4F81BD"/></a:accent1>
      <a:accent2><a:srgbClr val="C0504D"/></a:accent2>
      <a:accent3><a:srgbClr val="9BBB59"/></a:accent3>
      <a:accent4><a:srgbClr val="8064A2"/></a:accent4>
      <a:accent5><a:srgbClr val="4BACC6"/></a:accent5>
      <a:accent6><a:srgbClr val="F79646"/></a:accent6>
      <a:hlink><a:srgbClr val="0000FF"/></a:hlink>
      <a:folHlink><a:srgbClr val="800080"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont>
        <a:latin typeface="Calibri"/>
      </a:majorFont>
      <a:minorFont>
        <a:latin typeface="Calibri"/>
      </a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst/>
      <a:lnStyleLst/>
      <a:effectStyleLst/>
      <a:bgFillStyleLst/>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>'''
    pptx.writestr('ppt/theme/theme1.xml', xml_content)


def _create_slide_with_content(slide_num: int, title: str, content_items: List[str]) -> str:
    """Create a slide XML with title and bullet points."""
    # Build text content with proper spacing
    bullet_paragraphs = ""
    for item in content_items:
        bullet_paragraphs += f'''
        <a:p>
          <a:pPr lvl="0" marL="0" indent="0">
            <a:buFont typeface="Arial" pitchFamily="34" charset="0"/>
            <a:buChar char="•"/>
          </a:pPr>
          <a:r>
            <a:rPr lang="en-US" sz="2000" dirty="0"/>
            <a:t>{_escape_xml(item)}</a:t>
          </a:r>
          <a:endParaRPr lang="en-US" sz="2000" dirty="0"/>
        </a:p>'''
    
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" 
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" 
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      
      <!-- Title Shape -->
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Title 1"/>
          <p:cNvSpPr>
            <a:spLocks noGrp="1"/>
          </p:cNvSpPr>
          <p:nvPr>
            <p:ph type="title"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="457200" y="274638"/>
            <a:ext cx="8229600" cy="1143000"/>
          </a:xfrm>
        </p:spPr>
        <p:txBody>
          <a:bodyPr anchor="ctr"/>
          <a:lstStyle/>
          <a:p>
            <a:pPr algn="ctr"/>
            <a:r>
              <a:rPr lang="en-US" sz="4400" b="1" dirty="0"/>
              <a:t>{_escape_xml(title)}</a:t>
            </a:r>
            <a:endParaRPr lang="en-US" sz="4400"/>
          </a:p>
        </p:txBody>
      </p:sp>
      
      <!-- Content Shape -->
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="3" name="Content Placeholder 2"/>
          <p:cNvSpPr>
            <a:spLocks noGrp="1"/>
          </p:cNvSpPr>
          <p:nvPr>
            <p:ph type="body" idx="1"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr>
          <a:xfrm>
            <a:off x="457200" y="1600200"/>
            <a:ext cx="8229600" cy="4525963"/>
          </a:xfrm>
        </p:spPr>
        <p:txBody>
          <a:bodyPr anchor="t">
            <a:normAutofit fontScale="90000" lnSpcReduction="20000"/>
          </a:bodyPr>
          <a:lstStyle>
            <a:lvl1pPr marL="0" indent="0">
              <a:buFont typeface="Arial" pitchFamily="34" charset="0"/>
              <a:buChar char="•"/>
            </a:lvl1pPr>
          </a:lstStyle>
          {bullet_paragraphs}
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sld>'''


def _escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))


def _add_slide_rels(pptx: zipfile.ZipFile, slide_num: int):
    """Add relationship file for a slide."""
    rels_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''
    pptx.writestr(f'ppt/slides/_rels/slide{slide_num}.xml.rels', rels_content)


def _add_title_slide(pptx: zipfile.ZipFile, data):
    """Slide 1: Title slide."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = [
        f"Repository: {data.name}",
        f"Path: {data.path}",
        f"Analysis Date: {timestamp}",
        "Generated by RepoDoctor"
    ]
    slide_xml = _create_slide_with_content(1, "RepoDoctor Analysis Report", content)
    pptx.writestr('ppt/slides/slide1.xml', slide_xml)
    _add_slide_rels(pptx, 1)


def _add_overview_slide(pptx: zipfile.ZipFile, data):
    """Slide 2: Project Overview."""
    total_files = len(data.files)
    total_lines = sum(f.lines for f in data.files if not f.is_binary)
    languages = {}
    for f in data.files:
        if f.language and f.language != "Unknown":
            languages[f.language] = languages.get(f.language, 0) + 1
    
    content = [
        f"Total Files: {total_files}",
        f"Total Lines of Code: {total_lines:,}",
        f"Languages Detected: {len(languages)}",
        f"Primary Languages: {', '.join(list(languages.keys())[:5])}" if languages else "No languages detected"
    ]
    
    slide_xml = _create_slide_with_content(2, "Project Overview", content)
    pptx.writestr('ppt/slides/slide2.xml', slide_xml)
    _add_slide_rels(pptx, 2)


def _add_statistics_slide(pptx: zipfile.ZipFile, data):
    """Slide 3: Repository Statistics."""
    code_lines = sum(f.metrics.code_lines for f in data.files if f.metrics and f.metrics.code_lines)
    comment_lines = sum(f.metrics.comment_lines for f in data.files if f.metrics and f.metrics.comment_lines)
    blank_lines = sum(f.metrics.blank_lines for f in data.files if f.metrics and f.metrics.blank_lines)
    total_functions = sum(f.metrics.num_functions for f in data.files if f.metrics and f.metrics.num_functions)
    total_classes = sum(f.metrics.num_classes for f in data.files if f.metrics and f.metrics.num_classes)
    
    content = [
        f"Code Lines: {code_lines:,}",
        f"Comment Lines: {comment_lines:,}",
        f"Blank Lines: {blank_lines:,}",
        f"Total Functions: {total_functions:,}",
        f"Total Classes: {total_classes:,}"
    ]
    
    slide_xml = _create_slide_with_content(3, "Code Statistics", content)
    pptx.writestr('ppt/slides/slide3.xml', slide_xml)
    _add_slide_rels(pptx, 3)


def _add_architecture_slide(pptx: zipfile.ZipFile, data):
    """Slide 4: Architecture & Structure."""
    content = []
    
    if data.structure:
        content.append(f"README Present: {'Yes' if data.structure.get('README') == 'PASS' else 'No'}")
        content.append(f"Tests Directory: {'Yes' if data.structure.get('Tests') == 'PASS' else 'No'}")
        content.append(f".gitignore Present: {'Yes' if data.structure.get('.gitignore') == 'PASS' else 'No'}")
        content.append(f"License File: {'Yes' if data.structure.get('LICENSE') == 'PASS' else 'No'}")
    else:
        content.append("Structure analysis not available")
    
    if data.git and isinstance(data.git, dict):
        if data.git.get('available'):
            content.append(f"Git Repository: Active ({data.git.get('branch', 'unknown')} branch)")
        else:
            content.append("Git Repository: Not detected")
    elif hasattr(data.git, 'available'):
        if data.git.available:
            content.append(f"Git Repository: Active ({data.git.branch} branch)")
        else:
            content.append("Git Repository: Not detected")
    else:
        content.append("Git Repository: Not detected")
    
    slide_xml = _create_slide_with_content(4, "Project Architecture", content)
    pptx.writestr('ppt/slides/slide4.xml', slide_xml)
    _add_slide_rels(pptx, 4)


def _add_quality_slide(pptx: zipfile.ZipFile, data):
    """Slide 5: Code Quality Findings."""
    todo_count = len(data.todos) if data.todos else 0
    duplicate_count = len(data.duplicates) if data.duplicates else 0
    
    # Count files with high complexity
    complex_files = sum(1 for f in data.files if f.metrics and f.metrics.max_nesting and f.metrics.max_nesting > 4)
    
    content = [
        f"Health Score: {data.score.score if data.score else 'N/A'}/100",
        f"TODO/FIXME Markers: {todo_count}",
        f"Duplicate Code Blocks: {duplicate_count}",
        f"High Complexity Files: {complex_files}",
        "Overall Status: " + ("Good" if data.score and data.score.score >= 80 else "Needs Improvement" if data.score and data.score.score >= 60 else "Critical")
    ]
    
    slide_xml = _create_slide_with_content(5, "Code Quality", content)
    pptx.writestr('ppt/slides/slide5.xml', slide_xml)
    _add_slide_rels(pptx, 5)


def _add_security_slide(pptx: zipfile.ZipFile, data):
    """Slide 6: Security Analysis."""
    security_count = len(data.security) if data.security else 0
    
    content = [
        f"Security Findings: {security_count}",
    ]
    
    if security_count > 0:
        content.append(f"Potential secrets detected: {security_count}")
        content.append("Review required for credential exposure")
        content.append("Check .env files and API keys")
    else:
        content.append("No obvious security issues detected")
        content.append("Manual security audit still recommended")
    
    content.append("Note: Automated scan has limitations")
    
    slide_xml = _create_slide_with_content(6, "Security Analysis", content)
    pptx.writestr('ppt/slides/slide6.xml', slide_xml)
    _add_slide_rels(pptx, 6)


def _add_recommendations_slide(pptx: zipfile.ZipFile, data):
    """Slide 7: Recommendations."""
    content = []
    
    # Generate recommendations based on findings
    if not data.structure or data.structure.get('README') != 'PASS':
        content.append("Add a comprehensive README.md file")
    
    if not data.structure or data.structure.get('Tests') != 'PASS':
        content.append("Implement automated tests")
    
    if data.todos and len(data.todos) > 10:
        content.append(f"Address {len(data.todos)} TODO/FIXME items")
    
    if data.duplicates and len(data.duplicates) > 0:
        content.append("Refactor duplicate code blocks")
    
    if data.security and len(data.security) > 0:
        content.append("Review and secure exposed credentials")
    
    if not content:
        content.append("Good work! No critical issues found")
        content.append("Continue following best practices")
        content.append("Regular code reviews recommended")
    
    slide_xml = _create_slide_with_content(7, "Recommendations", content)
    pptx.writestr('ppt/slides/slide7.xml', slide_xml)
    _add_slide_rels(pptx, 7)


def _add_summary_slide(pptx: zipfile.ZipFile, data):
    """Slide 8: Summary."""
    score_text = f"{data.score.score}/100" if data.score else "N/A"
    
    content = [
        f"Final Health Score: {score_text}",
        f"Total Files Analyzed: {len(data.files)}",
        f"Analysis Complete",
        "",
        "Thank you for using RepoDoctor!",
        "For more information, run: repodoctor --help"
    ]
    
    slide_xml = _create_slide_with_content(8, "Summary", content)
    pptx.writestr('ppt/slides/slide8.xml', slide_xml)
    _add_slide_rels(pptx, 8)
