// src/lib.rs

use std::str;
use std::mem;
use std::ffi::{CString, CStr};
use std::os::raw::{c_char, c_void};
use std::slice;
use std::ptr;

// --- 内存管理 ---
// 这个函数由WASM导出，供Python宿主调用，以便在WASM的线性内存中分配空间。
#[no_mangle]
pub extern "C" fn allocate_memory(size: usize) -> *mut c_void {
    let mut buffer = Vec::with_capacity(size);
    let ptr = buffer.as_mut_ptr();
    // 告诉Rust不要管理这块内存的生命周期，因为所有权将交给宿主。
    mem::forget(buffer); 
    ptr
}

// 这个函数也由WASM导出，供Python宿主调用，以释放之前分配的内存。
#[no_mangle]
pub extern "C" fn free_memory(ptr: *mut c_void, size: usize) {
    unsafe {
        let _ = Vec::from_raw_parts(ptr, 0, size);
    }
}


// --- 核心逻辑 ---
// 这是WASM模块的主入口点，由Python宿主调用。
#[no_mangle]
pub extern "C" fn run(ptr: *mut u8, len: usize) -> u64 {
    // 1. 从宿主传递的指针和长度，安全地读取输入字符串。
    let input_bytes = unsafe { slice::from_raw_parts(ptr, len) };
    let input_str = match str::from_utf8(input_bytes) {
        Ok(s) => s,
        Err(_) => "Invalid UTF-8 input",
    };

    // 2. 执行核心业务逻辑（这里只是简单地拼接字符串）。
    let output_str = format!("{} - processed by Rust/WASM", input_str);

    // 3. 将输出字符串转换为C风格的字符串，准备返回给宿主。
    let c_output = CString::new(output_str).unwrap();
    let output_bytes = c_output.as_bytes_with_nul();
    let output_len = output_bytes.len();

    // 4. 在WASM内存中为输出分配空间，并拷贝数据。
    let output_ptr = allocate_memory(output_len) as *mut u8;
    unsafe {
        ptr::copy_nonoverlapping(output_bytes.as_ptr(), output_ptr, output_len);
    }

    // 5. 将指针和长度打包到一个64位整数中返回。
    //    高32位存指针，低32位存长度。
    //    这是在WASM和宿主间传递多个返回值的常用技巧。
    let packed_result: u64 = ((output_ptr as u64) << 32) | (output_len as u64);
    
    packed_result
}