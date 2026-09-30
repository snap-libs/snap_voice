# CPU Benchmark for SNAP TN (Text Normalization & Phonology Engine)

> **[Notice: Pure CPU Benchmark (Zero-GPU)]**  
> All benchmark results in this document were measured strictly on pure CPU (0.00% GPU engagement) using the ONNX Runtime CPU Execution Provider.

- **Document Version**: v1.3.0
- **Benchmark Date**: 2026-09-30
- **Engine**: SNAP C++ Native Engine v2.3.0
- **Runtime Environment**: C++17 Native, Linux x86_64, ONNX Runtime 1.18.1 CPU Execution Provider

---

## 1. Executive Summary

This document provides empirical CPU hardware benchmark data for the SNAP (Semantic Normalization via Attached Probes) C++ native Text Normalization (TN) and Phonology (G2P) engine.

The benchmark evaluated four CPUs with distinct clock frequencies, cache topologies, and vector instruction extensions using an identical C++ native test suite to measure empirical performance across different hardware characteristics.

---

## 2. Test Hardware Specifications

*(Note: GPUs were completely unused across all test environments; all workloads ran strictly on CPU threads)*

| CPU Model | Microarchitecture | Cores / Threads | Boost Clock | L3 Cache Structure | CPU SIMD Vector Unit |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Intel Core i7-13700KF** | Raptor Lake (10nm) | 16C / 24T | 5.4 GHz | 30 MB (Unified shared) | AVX2 (256-bit) |
| **AMD Dual EPYC 9334** | Zen 4 Server (5nm) | 64C / 128T | 3.5 GHz | 256 MB (32MB × 8 Slices) | AVX-512 (256-bit double-pumped) |
| **AMD Ryzen 7 7800X3D** | Zen 4 Desktop (5nm) | 8C / 16T | 5.0 GHz | 96 MB (Single CCD 3D Stacked) | AVX-512 (256-bit double-pumped) |
| **AMD Ryzen 9 9950X** | Zen 5 Desktop (4nm) | 16C / 32T | 5.7 GHz | 64 MB (32MB × 2 CCDs) | 512-bit Native Pipeline |

---

## 3. Empirical Benchmark Results (Pure CPU)

Measured at the C++ native level with high-resolution timers on real-world complex conversational sentence streams after 10 warmup iterations.

| CPU Model | Mean Latency | Median Latency (P50) | 99th Percentile Latency (P99) | Sequential Throughput (Single FPS) | Max Batch Throughput (Batch FPS) | Per-Sentence Latency at Optimal Batch |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Intel Core i7-13700KF** | `1.609 ms` | `1.488 ms` | `3.761 ms` | `621.3 FPS` | `661.9 FPS` (B64) | `1.510 ms` |
| **AMD Dual EPYC 9334** | `3.470 ms` | `3.268 ms` | `8.138 ms` | `288.1 FPS` | `746.5 FPS` (B128) | `1.339 ms` |
| **AMD Ryzen 7 7800X3D** | `1.078 ms` | `1.017 ms` | `1.351 ms` | `927.7 FPS` | `977.5 FPS` (B64) | `1.023 ms` |
| **AMD Ryzen 9 9950X** | `0.954 ms` | `0.898 ms` | `1.276 ms` | `1,047.5 FPS` | `1,447.8 FPS` (B32) | `0.690 ms` |

---

## 4. Benchmark Observations

Empirical results showed that all tested CPU environments delivered sufficient throughput for real-time text normalization. Specific observations based on hardware characteristics were as follows:

* **L3 Cache**: The runtime memory footprint of the SNAP engine is approximately **100 – 130 MB**. When the L3 cache accessible by a core accommodates this working set, DRAM accesses are minimized, contributing to a stabilized P99 tail latency.
* **Vector Execution Units**: Neural network matrix multiplications account for a significant portion of execution time; processors supporting 512-bit vector instructions (AVX-512) and 8-bit integer operations (VNNI) exhibited higher batch throughput.
* **Clock Frequency**: Single-sentence sequential latency was directly influenced by single-core boost clock frequencies rather than the total core count.
