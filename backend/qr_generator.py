import qrcode
import os
from PIL import Image

class QRCodeGenerator:
    def __init__(self, output_dir='qr_codes'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def generate_event_qr(self, event_id, registration_url):
        """Generate QR code for event registration"""
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        # Add registration URL
        qr.add_data(registration_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        filename = f"event_{event_id}_qr.png"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath)
        
        print(f"✅ QR code generated: {filepath}")
        return filepath
    
    def generate_qr_with_logo(self, event_id, registration_url, logo_path=None):
        """Generate QR code with optional logo in center"""
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        qr.add_data(registration_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        # Add logo if provided
        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path)
            
            # Calculate logo size (10% of QR code)
            qr_width, qr_height = img.size
            logo_size = min(qr_width, qr_height) // 5
            
            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Calculate position (center)
            logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            
            # Paste logo
            img.paste(logo, logo_pos)
        
        # Save
        filename = f"event_{event_id}_qr.png"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath)
        
        print(f"✅ QR code with logo generated: {filepath}")
        return filepath

# Singleton instance
qr_generator = QRCodeGenerator()