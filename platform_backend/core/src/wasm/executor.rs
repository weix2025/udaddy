use wasmtime::{Config, Engine, Module, Store, Linker, Instance};
use wasi_common::sync::WasiCtxBuilder;
use crate::error::{Result, Error};

pub struct WasmExecutor {
    engine: Engine,
}

impl WasmExecutor {
    pub fn new() -> Result<Self> {
        let mut config = Config::new();
        config.consume_fuel(true);
        let engine = Engine::new(&config)?;
        Ok(Self { engine })
    }

    pub fn execute(&self, wasm_module: &[u8], input_data: &[u8]) -> Result<Vec<u8>> {
        let module = Module::from_binary(&self.engine, wasm_module)?;
        
        let mut linker = Linker::new(&self.engine);
        wasi_common::sync::add_to_linker(&mut linker, |s| s)?;

        let wasi = WasiCtxBuilder::new()
            .inherit_stdio()
            .build();

        let mut store = Store::new(&self.engine, wasi);
        store.set_fuel(1_000_000)?;

        let instance = linker.instantiate(&mut store, &module)?;
        
        let memory = instance.get_memory(&mut store, "memory").ok_or_else(|| Error::WasmMemory("Memory not found".to_string()))?;
        memory.write(&mut store, 0, input_data).map_err(|e| Error::WasmMemory(e.to_string()))?;

        let main_func = instance.get_typed_func::<(), ()>(&mut store, "_start")?;
        main_func.call(&mut store, ())?;

        let mut output_buffer = vec![0u8; 1024];
        memory.read(&store, 0, &mut output_buffer).map_err(|e| Error::WasmMemory(e.to_string()))?;

        Ok(output_buffer)
    }
}