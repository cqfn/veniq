package org.springframework.messaging.rsocket;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.ByteBufAllocator;
import io.netty.buffer.CompositeByteBuf;
import io.rsocket.metadata.CompositeMetadataFlyweight;
import io.rsocket.metadata.TaggingMetadataFlyweight;
import io.rsocket.metadata.WellKnownMimeType;
import reactor.core.publisher.Mono;
import org.springframework.core.ReactiveAdapter;
import org.springframework.core.ResolvableType;
import org.springframework.core.codec.Encoder;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.core.io.buffer.DataBufferFactory;
import org.springframework.core.io.buffer.NettyDataBufferFactory;
import org.springframework.lang.Nullable;
import org.springframework.util.Assert;
import org.springframework.util.CollectionUtils;
import org.springframework.util.MimeType;
import org.springframework.util.ObjectUtils;
final class MetadataEncoder {
	private static final Pattern VARS_PATTERN = Pattern.compile("\\{(.+?)}");
	private static final Object NO_VALUE = new Object();
	private final MimeType metadataMimeType;
	private final RSocketStrategies strategies;
	private final boolean isComposite;
	private final ByteBufAllocator allocator;
	@Nullable
	private String route;
	private final List<MetadataEntry> metadataEntries = new ArrayList<>(4);
	private boolean hasAsyncValues;
	MetadataEncoder(MimeType metadataMimeType, RSocketStrategies strategies) {
		Assert.notNull(metadataMimeType, "'metadataMimeType' is required");
		Assert.notNull(strategies, "RSocketStrategies is required");
		this.metadataMimeType = metadataMimeType;
		this.strategies = strategies;
		this.isComposite = this.metadataMimeType.toString().equals(
				WellKnownMimeType.MESSAGE_RSOCKET_COMPOSITE_METADATA.getString());
		this.allocator = bufferFactory() instanceof NettyDataBufferFactory ?
				((NettyDataBufferFactory) bufferFactory()).getByteBufAllocator() : ByteBufAllocator.DEFAULT;
	}
	private DataBufferFactory bufferFactory() {
		return this.strategies.dataBufferFactory();
	}
	public MetadataEncoder route(String route, Object... routeVars) {
		this.route = expand(route, routeVars);
		if (!this.isComposite) {
			int count = this.route != null ? this.metadataEntries.size() + 1 : this.metadataEntries.size();
			Assert.isTrue(count < 2, "Composite metadata required for multiple metadata entries.");
		}
		return this;
	}

}