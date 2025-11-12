import os
import zipfile
from xml.dom import minidom

def create_pptx():
    # สร้างโครงสร้าง PPTX
    pptx_structure = {
        '[Content_Types].xml': '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide.main+xml"/>
<Override PartName="/ppt/slides/slide2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide.main+xml"/>
<Override PartName="/ppt/slides/slide3.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide.main+xml"/>
<Override PartName="/ppt/slides/slide4.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide.main+xml"/>
<Override PartName="/ppt/slides/slide5.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide.main+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout.main+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster.main+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>''',
        
        '_rels/.rels': '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>''',
        
        'ppt/_rels/presentation.xml.rels': '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/>
<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide3.xml"/>
<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide4.xml"/>
<Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide5.xml"/>
<Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
</Relationships>''',
        
        'ppt/presentation.xml': '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></p:sldMasterIdLst>
<p:sldIdLst>
<p:sldId id="256" r:id="rId2" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
<p:sldId id="257" r:id="rId3" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
<p:sldId id="258" r:id="rId4" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
<p:sldId id="259" r:id="rId5" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
<p:sldId id="260" r:id="rId6" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
</p:sldIdLst>
<p:sldSz cx="9144000" cy="6858000"/>
</p:presentation>'''
    }
    
    # Slides content
    slides = [
        ("SupplyUse Stock Management System", "ระบบจัดการสต๊อกสินค้าแบบครบวงจร\n\nPTG Hackathon 2024\nFlask Web Application"),
        ("📋 ภาพรวมโปรเจค", "🎯 วัตถุประสงค์\n• จัดการสต๊อกสินค้าอย่างมีประสิทธิภาพ\n• ติดตามการเคลื่อนไหวสินค้าเข้า-ออก\n• สร้างรายงานและสถิติการใช้งาน\n• รองรับการสแกนบาร์โค้ดและค้นหาด้วยภาพ"),
        ("🏗️ สถาปัตยกรรมระบบ", "เทคโนโลยีที่ใช้\n• Backend: Python Flask\n• Database: SQLite\n• Frontend: HTML, CSS, JavaScript\n• UI Framework: Bootstrap\n\nโครงสร้างฐานข้อมูล\n• products: สินค้า\n• stock_movements: การเคลื่อนไหว\n• users: ผู้ใช้งาน"),
        ("✨ ฟีเจอร์หลัก", "📦 จัดการสินค้า\n• เพิ่ม/แก้ไข/ลบสินค้า\n• อัพโหลดรูปภาพสินค้า\n• กำหนดสต๊อกขั้นต่ำ\n\n📥📤 จัดการสต๊อก\n• รับสินค้าเข้า (Stock In)\n• เบิกสินค้าออก (Stock Out)\n• ระบบเลขที่เอกสาร"),
        ("🎉 สรุป", "SupplyUse Stock Management System\nเป็นโซลูชันที่ครบครันสำหรับการจัดการสต๊อกสินค้า\n\nKey Benefits\n✅ ลดต้นทุนการจัดการ\n✅ เพิ่มประสิทธิภาพการทำงาน\n✅ ข้อมูลแม่นยำและทันสมัย\n✅ รองรับการเติบโตของธุรกิจ")
    ]
    
    # สร้าง slide files
    for i, (title, content) in enumerate(slides, 1):
        slide_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld>
<p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr/>
<p:sp>
<p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr><a:spLocks noGrp="1" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/></p:cNvSpPr><p:nvPr><p:ph type="ctrTitle"/></p:nvPr></p:nvSpPr>
<p:spPr/>
<p:txBody>
<a:bodyPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>
<a:lstStyle xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>
<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
<a:r><a:t>{title}</a:t></a:r>
</a:p>
</p:txBody>
</p:sp>
<p:sp>
<p:nvSpPr><p:cNvPr id="3" name="Content"/><p:cNvSpPr><a:spLocks noGrp="1" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/></p:cNvSpPr><p:nvPr><p:ph idx="1"/></p:nvPr></p:nvSpPr>
<p:spPr/>
<p:txBody>
<a:bodyPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>
<a:lstStyle xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>
<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
<a:r><a:t>{content}</a:t></a:r>
</a:p>
</p:txBody>
</p:sp>
</p:spTree>
</p:cSld>
</p:sld>'''
        pptx_structure[f'ppt/slides/slide{i}.xml'] = slide_xml
    
    # เพิ่มไฟล์ที่จำเป็น
    pptx_structure['ppt/slideMasters/slideMaster1.xml'] = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></p:sldLayoutIdLst>
</p:sldMaster>'''
    
    pptx_structure['ppt/slideLayouts/slideLayout1.xml'] = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
</p:sldLayout>'''
    
    pptx_structure['ppt/theme/theme1.xml'] = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
<a:themeElements>
<a:clrScheme name="Office"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1></a:clrScheme>
<a:fontScheme name="Office"><a:majorFont><a:latin typeface="Calibri Light"/></a:majorFont><a:minorFont><a:latin typeface="Calibri"/></a:minorFont></a:fontScheme>
<a:fmtScheme name="Office"/>
</a:themeElements>
</a:theme>'''
    
    # สร้างไฟล์ PPTX
    with zipfile.ZipFile('docs/SupplyUse_Complete_Presentation.pptx', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename, content in pptx_structure.items():
            zipf.writestr(filename, content)
    
    print("สร้างไฟล์ PowerPoint เรียบร้อยแล้ว: docs/SupplyUse_Complete_Presentation.pptx")

if __name__ == "__main__":
    create_pptx()