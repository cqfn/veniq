public abstract class Test {
	private static final EntityResolver NO_OP_ENTITY_RESOLVER =
			(publicId, systemId) -> new InputSource(new StringReader(""));

	/** Logger available to subclasses. */
	protected final Log logger = LogFactory.getLog(getClass());

	private boolean supportDtd = false;

	private boolean processExternalEntities = false;

	@Nullable
	private DocumentBuilderFactory documentBuilderFactory;

	private final Object documentBuilderFactoryMonitor = new Object();
	
	protected Document buildDocument() {
		try {
			DocumentBuilder documentBuilder;
			synchronized (this.documentBuilderFactoryMonitor) {
				if (this.documentBuilderFactory == null) {
					factory.setValidating(false);
					factory.setNamespaceAware(true);
					factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", !isSupportDtd());
					factory.setFeature("http://xml.org/sax/features/external-general-entities", isProcessExternalEntities());
					this.documentBuilderFactory = factory;
				}
				documentBuilder = createDocumentBuilder(this.documentBuilderFactory);
			}
			return documentBuilder.newDocument();
		}
		catch (ParserConfigurationException ex) {
			throw new UnmarshallingFailureException("Could not create document placeholder: " + ex.getMessage(), ex);
		}
	}

	protected DocumentBuilderFactory createDocumentBuilderFactory() throws ParserConfigurationException {
		DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
		factory.setValidating(false);
		factory.setNamespaceAware(true);
		factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", !isSupportDtd());
		factory.setFeature("http://xml.org/sax/features/external-general-entities", isProcessExternalEntities());
		return factory;
	}
	
}