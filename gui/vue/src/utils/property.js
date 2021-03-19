export function getPropertyInfo(property, mainCollectionId, collections) {
    return new Array(Math.floor((property.length + 1) / 2))
        .fill(null)
        .map((_, idx) => {
            const collectionIdx = idx > 0 ? (idx * 2) - 1 : null;
            const propIdx = idx * 2;

            return {
                collectionIdx,
                collection: collectionIdx ? property[collectionIdx] : null,
                collections: getCollectionsForIndex(collectionIdx),
                propIdx,
                property: property[propIdx],
                properties: getPropertiesForIndex(propIdx),
            };
        });

    function getCollectionsForIndex(index) {
        if (index === null)
            return null;

        const properties = getPropertiesForIndex(index - 1);
        const prop = properties[property[index - 1]];
        return getReferencedCollections(prop.referencedCollections);
    }

    function getReferencedCollections(referencedCollections) {
        return referencedCollections
            .filter(collectionId => collections.hasOwnProperty(collectionId))
            .reduce((acc, collectionId) => {
                acc[collectionId] = collections[collectionId];
                return acc;
            }, {});
    }

    function getPropertiesForIndex(index) {
        const collectionId = index === 0 ? mainCollectionId : property[index - 1];
        return getPropertiesForCollection(collectionId, collections);
    }
}

export function getPropertiesForCollection(collectionId, collections) {
    if (!collections.hasOwnProperty(collectionId))
        return null;

    return {
        uri: {
            density: 100,
            isInverse: false,
            isLink: false,
            isList: false,
            isValueType: false,
            name: 'uri',
            referencedCollections: [],
            shortenedUri: 'uri',
            uri: 'uri'
        }, ...Object.fromEntries(
            Object
                .entries(collections[collectionId].properties)
                .sort(([idA, propA], [idB, propB]) => {
                    if (propA.shortenedUri && propB.shortenedUri) {
                        if (propA.shortenedUri === propA.uri && propB.shortenedUri !== propB.uri)
                            return 1;

                        if (propB.shortenedUri === propB.uri && propA.shortenedUri !== propA.uri)
                            return -1;

                        if (propA.shortenedUri === propB.shortenedUri)
                            return propB.isInverse ? -1 : 1;

                        return propA.shortenedUri < propB.shortenedUri ? -1 : 1;
                    }

                    return idA < idB ? -1 : 1;
                })
        )
    };
}
