SELECT
    -- creationTimestamp,
    -- fingerprint,
    -- gatewayAddress,
    -- id,
    ipCidrRange,
    kind,
    name,
    -- network,
    -- privateIpGoogleAccess,
    -- privateIpv6GoogleAccess,
    -- purpose,
    -- region,
    -- selfLink,
    -- stackType
FROM
    read_json_auto ('subnets.json');