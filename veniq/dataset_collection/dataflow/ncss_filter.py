from veniq.metrics.ncss.ncss import NCSSMetric


def filter_by_ncss(em_info):
    ast = em_info['ast']
    extracted_m_decl = em_info['extracted_m_decl']
    ncss = NCSSMetric().value(ast.get_subtree(extracted_m_decl))
    if ncss > 3:
        em_info['ncss_extracted'] = ncss
        ncss_target_node = NCSSMetric().value(ast.get_subtree(extracted_m_decl))
        em_info['ncss_target'] = ncss_target_node
        yield em_info