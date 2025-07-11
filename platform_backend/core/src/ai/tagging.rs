use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct Capability {
    pub input_type: String,
    pub output_type: String,
    pub formats: Vec<String>,
    pub max_resolution: Option<String>,
    // Other relevant metadata
}

pub fn semantic_distance(cap1: &Capability, cap2: &Capability) -> f32 {
    let mut distance = 0.0;

    if cap1.output_type != cap2.input_type {
        distance += 100.0; // Incompatible types
    }

    let format_overlap = cap1.formats.iter().filter(|f| cap2.formats.contains(f)).count();
    if format_overlap == 0 {
        distance += 10.0; // No common format
    }

    // This is a very basic example. A real-world implementation would
    // involve more sophisticated logic, potentially using embeddings
    // or a knowledge graph.
    
    distance
}