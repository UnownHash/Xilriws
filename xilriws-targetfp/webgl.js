import * as utils from "./utils.js"
import * as funcToString from "./funcToString.js"

export function block() {
    const glProto = WebGLRenderingContext.prototype
    const gl2Proto = WebGL2RenderingContext.prototype

    utils.overwriteProp(glProto, "getSupportedExtensions", () => ["ANGLE_instanced_arrays", "EXT_blend_minmax", "EXT_clip_control", "EXT_color_buffer_half_float", "EXT_depth_clamp", "EXT_disjoint_timer_query", "EXT_float_blend", "EXT_frag_depth", "EXT_polygon_offset_clamp", "EXT_shader_texture_lod", "EXT_texture_compression_bptc", "EXT_texture_compression_rgtc", "EXT_texture_filter_anisotropic", "EXT_texture_mirror_clamp_to_edge", "EXT_sRGB", "KHR_parallel_shader_compile", "OES_element_index_uint", "OES_fbo_render_mipmap", "OES_standard_derivatives", "OES_texture_float", "OES_texture_float_linear", "OES_texture_half_float", "OES_texture_half_float_linear", "OES_vertex_array_object", "WEBGL_blend_func_extended", "WEBGL_color_buffer_float", "WEBGL_compressed_texture_s3tc", "WEBGL_compressed_texture_s3tc_srgb", "WEBGL_debug_renderer_info", "WEBGL_debug_shaders", "WEBGL_depth_texture", "WEBGL_draw_buffers", "WEBGL_lose_context", "WEBGL_multi_draw", "WEBGL_polygon_mode"])
    utils.overwriteProp(gl2Proto, "getSupportedExtensions", () => ["ANGLE_instanced_arrays", "EXT_blend_minmax", "EXT_clip_control", "EXT_color_buffer_half_float", "EXT_depth_clamp", "EXT_disjoint_timer_query", "EXT_float_blend", "EXT_frag_depth", "EXT_polygon_offset_clamp", "EXT_shader_texture_lod", "EXT_texture_compression_bptc", "EXT_texture_compression_rgtc", "EXT_texture_filter_anisotropic", "EXT_texture_mirror_clamp_to_edge", "EXT_sRGB", "KHR_parallel_shader_compile", "OES_element_index_uint", "OES_fbo_render_mipmap", "OES_standard_derivatives", "OES_texture_float", "OES_texture_float_linear", "OES_texture_half_float", "OES_texture_half_float_linear", "OES_vertex_array_object", "WEBGL_blend_func_extended", "WEBGL_color_buffer_float", "WEBGL_compressed_texture_s3tc", "WEBGL_compressed_texture_s3tc_srgb", "WEBGL_debug_renderer_info", "WEBGL_debug_shaders", "WEBGL_depth_texture", "WEBGL_draw_buffers", "WEBGL_lose_context", "WEBGL_multi_draw", "WEBGL_polygon_mode"])

    const parameters = new Map()
    parameters.set(gl2Proto.MAX_VERTEX_UNIFORM_VECTORS, utils.randomChoose([127, 128, 255, 256, 511, 512, 1023, 1024, 2047, 2048, 4095, 4096]))
    parameters.set(gl2Proto.MAX_VIEWPORT_DIMS, utils.randomChoose([[16384, 16384], [32767, 32767], [65536, 65536]]))
    parameters.set(gl2Proto.RENDERER, utils.randomChoose(["WebKit WebGL", "WebKit WebGL", "WebKit WebGL", "WebKit WebGL", "ANGLE (Microsoft, Microsoft Basic Render Driver Direct3D11 vs_5_0 ps_5_0), or similar", "ANGLE (Intel, Intel(R) HD Graphics Direct3D11 vs_5_0 ps_5_0), or similar", "Adreno (TM) 650, or similar"]))

    const unmaskedVendor = utils.randomChoose([
        "Google Inc. (Microsoft)", "Google Inc. (Intel)", "Google Inc. (NVIDIA Corporation)", "Google Inc. (ARM)", "Google Inc. (NVIDIA)", "Google Inc. (AMD)"
    ])
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

    const unmaskedRenderer = "ANGLE(" + graphicsCard + " (0x0000" + randomHex + ") Direct3D11 vs_5_0 ps_5_0, D3D11)"

    const originalGetParameter = gl2Proto.getParameter
    gl2Proto.getParameter = function (parameter) {
        try {
            console.log("webgl: " + parameter)
            if (parameters.has(parameter)) {
                return parameters.get(parameter)
            }

            let debug = null
            try {
                debug = this.getExtension("WEBGL_debug_renderer_info")
            } catch (e) {
            }

            if (debug) {
                if (parameter === debug.UNMASKED_VENDOR_WEBGL) {
                    return unmaskedVendor
                } else if (parameter === debug.UNMASKED_RENDERER_WEBGL) {
                    return unmaskedRenderer
                }
            }
        } catch (e) {
            console.error(e)
        }


        return originalGetParameter.bind(this, parameter)()
    }
    glProto.getParameter = gl2Proto.getParameter

    const originalBufferData = gl2Proto.bufferData
    gl2Proto.bufferData = function (target, srcData, usage) {
        try {
            srcData[0] = utils.randomNumber(1, 5) * -0.1
            srcData[1] = utils.randomNumber(5, 9) * -0.1
            srcData[3] = utils.randomNumber(1, 9) * 0.1
        } catch(e) {
            console.error(e)
        }
        return originalBufferData.bind(this, target, srcData, usage)()
    }
    glProto.bufferData = gl2Proto.bufferData

    utils.setName(WebGLRenderingContext, "getSupportedExtensions")
    utils.setName(WebGLRenderingContext, "getParameter")
    utils.setName(WebGLRenderingContext, "bufferData")
    funcToString.set(glProto.getSupportedExtensions)
    funcToString.set(glProto.getParameter)
    funcToString.set(glProto.bufferData)

    utils.setName(WebGL2RenderingContext, "getSupportedExtensions")
    utils.setName(WebGL2RenderingContext, "getParameter")
    utils.setName(WebGL2RenderingContext, "bufferData")
    funcToString.set(gl2Proto.getSupportedExtensions)
    funcToString.set(gl2Proto.getParameter)
    funcToString.set(gl2Proto.bufferData)
}