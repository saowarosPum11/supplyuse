let codeReader = null;
let scanning = false;

function startBarcodeScanner() {
    const modal = new bootstrap.Modal(document.getElementById('scanner-modal'));
    const video = document.getElementById('scanner-video');
    
    modal.show();
    scanning = true;
    
    if (!codeReader) {
        codeReader = new ZXing.BrowserMultiFormatReader();
    }
    
    codeReader.getVideoInputDevices().then((videoInputDevices) => {
        const selectedDeviceId = videoInputDevices[0].deviceId;
        
        codeReader.decodeFromVideoDevice(selectedDeviceId, video, (result, err) => {
            if (result && scanning) {
                handleBarcodeResult(result.text);
                scanning = false;
                modal.hide();
                codeReader.reset();
            }
        });
    }).catch((err) => {
        console.error(err);
        alert('ไม่สามารถเข้าถึงกล้องได้');
    });
    
    document.getElementById('scanner-modal').addEventListener('hidden.bs.modal', function() {
        scanning = false;
        if (codeReader) {
            codeReader.reset();
        }
    });
}

async function handleBarcodeResult(barcode) {
    // For add/edit product pages
    const barcodeInput = document.querySelector('input[name="barcode"], #barcode');
    if (barcodeInput) {
        barcodeInput.value = barcode;
        return;
    }
    
    // For stock in/out pages - find product by barcode
    try {
        const response = await fetch('/scan_barcode', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({barcode: barcode})
        });
        
        const result = await response.json();
        
        if (result.success) {
            const productSelect = document.getElementById('product_id');
            productSelect.value = result.product.id;
            
            // Trigger change event to update stock info
            productSelect.dispatchEvent(new Event('change'));
            
            // Focus on quantity field
            document.getElementById('quantity').focus();
        } else {
            alert(result.error);
        }
    } catch (error) {
        alert('เกิดข้อผิดพลาดในการค้นหาสินค้า');
    }
}