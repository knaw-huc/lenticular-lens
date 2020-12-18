import React from 'react';
import {Collections, Dataset, Properties} from './dataset';

export interface PropertyProps {
    dataset: Dataset,
    datasetId: string,
    collectionId: string,
    property: string[],
    readOnly?: boolean,
    singular?: boolean,
    add?: () => void,
    remove?: () => void,
    entityTypeSelectionInfo?: boolean,
    onChange?: (oldProperty: string[], newProperty: string[]) => void;
}

export function Property(
    {
        dataset, datasetId, collectionId, property, add, remove, onChange,
        readOnly = false,
        singular = false,
        entityTypeSelectionInfo = true
    }: PropertyProps
) {
    const getPropertiesForIndex = (index: number): Properties | null => {
        const collId = index === 0 ? collectionId : property[index - 1];
        return getPropertiesForCollection(collId);
    };

    const getPropertiesForCollection = (collectionId: string): Properties | null => {
        return collectionId in dataset.collections ? dataset.collections[collectionId].properties : null;
    };

    const getCollectionsForIndex = (index: number | null): Collections | null => {
        if (index === null)
            return null;

        const properties = getPropertiesForIndex(index - 1);
        if (properties) {
            const prop = properties[property[index - 1]];
            return getReferencedCollections(prop.referencedCollections);
        }

        return null;
    };

    const getReferencedCollections = (referencedCollections: string[]): Collections => {
        return referencedCollections
            .filter(collectionId => collectionId in dataset.collections)
            .reduce<Collections>((acc, collectionId) => {
                acc[collectionId] = dataset.collections[collectionId];
                return acc;
            }, {});
    };

    const updateProperty = (newValue: string, index: number) => {
        if (onChange) {
            const newProperty = [...property];
            newProperty[index] = newValue;

            const length = newProperty.length;
            const collId = length > 2 ? newProperty[length - 2] : collectionId;
            const prop = newProperty[length - 1];

            if (newValue === '__value__')
                newProperty.splice(length - 1);

            const props = getPropertiesForCollection(collId);
            const properties = prop && props ? props[prop] : null;
            if (properties && properties.referencedCollections.length > 0)
                newProperty.push('', '');

            onChange(property, newProperty);
        }
    };

    const resetProperty = (index: number) => {
        if (onChange) {
            const newProperty = [...property];

            const replaceBy = (index % 2 === 1) ? ['', ''] : [''];
            newProperty.splice(index, (newProperty.length - index), ...replaceBy);

            onChange(property, newProperty);
        }
    };

    const properties = new Array(Math.floor((property.length + 1) / 2))
        .fill(null)
        .map((_, idx) => {
            const collectionIdx = idx > 0 ? (idx * 2) - 1 : null;
            const propIdx = idx * 2;

            return {
                key: `${collectionIdx}_${propIdx}`,
                collectionIdx,
                collection: collectionIdx ? property[collectionIdx] : null,
                collections: getCollectionsForIndex(collectionIdx),
                propIdx,
                property: property[propIdx],
                properties: getPropertiesForIndex(propIdx),
            };
        });

    return (
        <div className="property">
            {entityTypeSelectionInfo && <>
                <div className="property-pill property-resource">
                    {datasetId}
                </div>

                <div className="property-pill property-resource">
                    {collectionId}
                </div>

                {add && !singular && !readOnly &&
                <button className="property-button" title="Add another property" onClick={add}>
                    Add
                </button>}

                {remove && !singular && !readOnly &&
                <button className="property-button" title="Remove this property" onClick={remove}>
                    Remove
                </button>}
            </>
            }

            {properties.map(prop =>
                <React.Fragment key={prop.key}>
                    {prop.collections && <>
                        <div className="property-sep">→</div>

                        {prop.collection === '' && !readOnly &&
                        <button className="property-pill property-select"
                                onClick={_ => console.log(prop.collections)}>
                            Select value
                        </button>
                        }

                        {prop.collection && readOnly &&
                        <div className="property-pill property-prop">
                            {prop.collections[prop.collection].title || prop.collection}
                        </div>
                        }

                        {prop.collection && !readOnly &&
                        <button className="property-pill property-prop"
                                onClick={_ => prop.collectionIdx != null && resetProperty(prop.collectionIdx)}>
                            {prop.collections[prop.collection].title || prop.collection}
                        </button>
                        }
                    </>}

                    {prop.properties && prop.property !== '__value__' && <>
                        {prop.collection && <div className="property-sep">→</div>}

                        {prop.property === '' && !readOnly &&
                        <button className="property-pill property-select"
                                onClick={_ => console.log(prop.properties)}>
                            Select value
                        </button>
                        }

                        {prop.property && readOnly &&
                        <div className="property-pill">
                            {prop.properties[prop.property].isInverse && '← '}
                            {prop.properties[prop.property].shortenedUri}
                        </div>
                        }

                        {prop.property && !readOnly &&
                        <button className="property-pill property-prop"
                                onClick={_ => prop.propIdx != null && resetProperty(prop.propIdx)}>
                            {prop.properties[prop.property].isInverse && '← '}
                            {prop.properties[prop.property].shortenedUri}
                        </button>
                        }
                    </>}
                </React.Fragment>
            )}

            {!entityTypeSelectionInfo && !singular && !readOnly && (add || remove) &&
            <div className="property-buttons">
                {add && <button title="Add another property" onClick={add}>Add</button>}
                {remove && <button title="Remove this property" onClick={remove}>Remove</button>}
            </div>
            }
        </div>
    );
}