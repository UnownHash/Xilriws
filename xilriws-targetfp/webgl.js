import * as utils from "./utils.js"
import * as funcToString from "./funcToString.js"

export function block() {
    const glProto = WebGLRenderingContext.prototype

    utils.overwriteProp(glProto, "getSupportedExtensions", () => ["ANGLE_instanced_arrays","EXT_blend_minmax","EXT_clip_control","EXT_color_buffer_half_float","EXT_depth_clamp","EXT_disjoint_timer_query","EXT_float_blend","EXT_frag_depth","EXT_polygon_offset_clamp","EXT_shader_texture_lod","EXT_texture_compression_bptc","EXT_texture_compression_rgtc","EXT_texture_filter_anisotropic","EXT_texture_mirror_clamp_to_edge","EXT_sRGB","KHR_parallel_shader_compile","OES_element_index_uint","OES_fbo_render_mipmap","OES_standard_derivatives","OES_texture_float","OES_texture_float_linear","OES_texture_half_float","OES_texture_half_float_linear","OES_vertex_array_object","WEBGL_blend_func_extended","WEBGL_color_buffer_float","WEBGL_compressed_texture_s3tc","WEBGL_compressed_texture_s3tc_srgb","WEBGL_debug_renderer_info","WEBGL_debug_shaders","WEBGL_depth_texture","WEBGL_draw_buffers","WEBGL_lose_context","WEBGL_multi_draw","WEBGL_polygon_mode"])

    const originalGetParameter = glProto.getParameter
    glProto.getParameter = function (parameter) {
        if (parameter === glProto.MAX_VERTEX_UNIFORM_VECTORS) {
            return utils.randomChoose([127, 128, 255, 256, 511, 512, 1023, 1024, 2047, 2048, 4095, 4096])
        } else if (parameter === glProto.MAX_VIEWPORT_DIMS) {
            return utils.randomChoose([[16384, 16384], [32767, 32767], [65536, 65536]])
        } else if (parameter === glProto.RENDERER) {
            return utils.randomChoose(["WebKit WebGL", "WebKit WebGL", "WebKit WebGL", "WebKit WebGL", "ANGLE (Microsoft, Microsoft Basic Render Driver Direct3D11 vs_5_0 ps_5_0), or similar", "ANGLE (Intel, Intel(R) HD Graphics Direct3D11 vs_5_0 ps_5_0), or similar", "Adreno (TM) 650, or similar"])
        } else {
            const debug = this.getExtension("WEBGL_debug_renderer_info")
            if (debug) {
                if (parameter === debug.UNMASKED_VENDOR_WEBGL) {
                    return utils.randomChoose([
                        "Google Inc. (Microsoft)", "Google Inc. (Intel)", "Google Inc. (NVIDIA Corporation)", "Google Inc. (ARM)", "Google Inc. (NVIDIA)", "Google Inc. (AMD)"
                    ])
                } else if (parameter === debug.UNMASKED_RENDERER_WEBGL) {
                    let randomHex = ""
                    for (let i = 0; i < 4; i++) {
                        randomHex += utils.randomChoose(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E"])
                    }
                    const graphicsCard = utils.randomChoose([
                        "NVIDIA, NVIDIA GeForce MX450",
                        "NVIDIA, NVIDIA GeForce 710M",
                        "NVIDIA, NVIDIA GeForce RTX 2050",
                        "NVIDIA, NVIDIA GeForce GTX 950M",
                        "Intel, Intel(R) UHD Graphics 620",
                        "Intel, Intel(R) HD Graphics 630",
                        "Intel, Intel(R) UHD Graphics",
                        "Intel, Intel(R) Iris(R) Xe Graphics",
                        "AMD, Radeon RX 570 Series",
                        "AMD, Radeon R9 380 Series",
                        "AMD, Radeon X800 Series",
                    ])

                    return "ANGLE(" + graphicsCard + " (0x0000" + randomHex + ") Direct3D11 vs_5_0 ps_5_0, D3D11)"
                }
            }
        }
        return originalGetParameter.bind(this, parameter)()
    }

    utils.overwriteProp(glProto.getParameter, "name", "getParameter")

    funcToString.set(glProto.getSupportedExtensions)
    funcToString.set(glProto.getParameter)
}