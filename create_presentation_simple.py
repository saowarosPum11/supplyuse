import shutil
import os

def create_presentation_copy():
    template_path = 'docs/Template.pptx'
    output_path = 'docs/SupplyUse_Project_Presentation.pptx'
    
    if os.path.exists(template_path):
        # คัดลอกไฟล์ template
        shutil.copy2(template_path, output_path)
        print(f"สร้างไฟล์นำเสนอจาก template เรียบร้อยแล้ว: {output_path}")
        print("กรุณาเปิดไฟล์และแก้ไขเนื้อหาตามต้องการ")
    else:
        print(f"ไม่พบไฟล์ template: {template_path}")

if __name__ == "__main__":
    create_presentation_copy()