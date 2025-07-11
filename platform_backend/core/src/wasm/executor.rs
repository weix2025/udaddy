// Wasm执行器：封装wasmtime的核心逻辑。
// 负责加载Wasm模块、通过wasmtime::Store::add_fuel注入"Fuel"以防止无限循环、
// 配置WASI沙箱环境（特别是通过wasi_common::sync::Dir进行严格的文件系统目录映射，限制Agent的文件访问权限）、
// 并管理与Wasm模块的内存数据交换。