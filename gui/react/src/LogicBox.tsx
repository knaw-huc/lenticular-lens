import React from 'react';

export type LogicBox<K extends string, E> = { type: string } & { [name in K]: (LogicBox<K, E> | E)[] };

export interface LogicBoxProps<K extends string, E> {
    logicBox: LogicBox<K, E>,
    elementsName: K,
    render: (type: string, index: number, element: E, add: () => void, remove: () => void) => React.ReactElement,
    add?: () => E,
    onChange?: (oldLogicBox: LogicBox<K, E>, newLogicBox: LogicBox<K, E>) => void,
    options?: { [key: string]: string },
    optionGroups?: { [group: string]: string[] },
    optionDescriptions?: { [key: string]: string },
    exactNumberOfElements?: number,
}

export function LogicBox<K extends string, E>(
    {
        logicBox, elementsName, render, add, onChange, exactNumberOfElements,
        options = {
            'AND': 'All conditions must be met (AND)',
            'OR': 'At least one of the conditions must be met (OR)'
        },
        optionGroups = {},
        optionDescriptions = {},
    }: LogicBoxProps<K, E>
) {
    return <LogicBoxLeaf
        rootLogicBox={logicBox}
        logicBox={logicBox}
        elementsName={elementsName}
        render={render}
        add={add}
        index={-1}
        parentType={null}
        parentIndexes={[]}
        options={options}
        optionGroups={optionGroups}
        optionDescriptions={optionDescriptions}
        exactNumberOfElements={exactNumberOfElements}
        onChange={onChange}
    />;
}

interface LogicBoxLeafProps<K extends string, E> {
    rootLogicBox: LogicBox<K, E>,
    logicBox: LogicBox<K, E> | E,
    elementsName: K,
    render: (type: string, index: number, element: E, add: () => void, remove: () => void) => React.ReactElement,
    add?: () => E,
    index: number,
    parentType: string | null,
    parentIndexes: number[],
    options: { [key: string]: string },
    optionGroups: { [group: string]: string[] },
    optionDescriptions: { [key: string]: string },
    exactNumberOfElements?: number,
    onChange?: (oldLogicBox: LogicBox<K, E>, newLogicBox: LogicBox<K, E>) => void,
}

function LogicBoxLeaf<K extends string, E>(
    {
        rootLogicBox, logicBox, elementsName, render, add, index, parentType, parentIndexes,
        options, optionGroups, optionDescriptions, exactNumberOfElements, onChange
    }: LogicBoxLeafProps<K, E>
) {
    const isLogicBox = (element: LogicBox<K, E> | E): element is LogicBox<K, E> =>
        'type' in logicBox && elementsName in logicBox;

    const goToLeaf = (logicBox: LogicBox<K, E>, indexPath: number[]): LogicBox<K, E> =>
        indexPath.reduce((leaf, index) =>
            leaf[elementsName][index] as LogicBox<K, E>, logicBox);

    const changeType = (newType: string) => {
        if (onChange) {
            const logicBoxNew = JSON.parse(JSON.stringify(rootLogicBox));
            const leaf = goToLeaf(logicBoxNew, index >= 0 ? [...parentIndexes, index] : parentIndexes);
            leaf.type = newType;

            onChange(rootLogicBox, logicBoxNew);
        }
    };

    const addElement = () => {
        let elements = (logicBox as LogicBox<K, E>)[elementsName];
        if (add && onChange && (!exactNumberOfElements || elements.length < exactNumberOfElements)) {
            const logicBoxNew = JSON.parse(JSON.stringify(rootLogicBox));
            const leaf = goToLeaf(logicBoxNew, index >= 0 ? [...parentIndexes, index] : parentIndexes);

            leaf[elementsName].push(add());

            elements = (logicBoxNew as LogicBox<K, E>)[elementsName];
            while (exactNumberOfElements && elements.length < exactNumberOfElements)
                leaf[elementsName].push(add());

            onChange(rootLogicBox, logicBoxNew);
        }
    };

    const removeElement = () => {
        if (onChange && index >= 0) {
            const logicBoxNew = JSON.parse(JSON.stringify(rootLogicBox));
            const leaf = goToLeaf(logicBoxNew, parentIndexes);

            if (exactNumberOfElements) {
                const node = leaf[elementsName][index];
                if (isLogicBox(node))
                    leaf[elementsName][index] = node[elementsName][0];
            }
            else {
                leaf[elementsName].splice(index, 1);
                if (parentIndexes.length > 0 && leaf[elementsName].length === 1) {
                    const parentLeaf = goToLeaf(logicBoxNew, parentIndexes.slice(0, -1));
                    parentLeaf[elementsName][parentIndexes[0]] = leaf[elementsName][0];
                }
            }

            onChange(rootLogicBox, logicBoxNew);
        }
    };

    const createLeaf = () => {
        if (add && onChange && index >= 0) {
            const logicBoxNew = JSON.parse(JSON.stringify(rootLogicBox));
            const leaf = goToLeaf(logicBoxNew, parentIndexes);

            leaf[elementsName][index] = {
                type: Object.keys(options)[0],
                [elementsName]: [leaf[elementsName][index], add()],
            } as LogicBox<K, E>;

            onChange(rootLogicBox, logicBoxNew);
        }
    };

    if (!isLogicBox(logicBox))
        return render(parentType as string, index, logicBox, createLeaf, removeElement);

    return (
        <div className={index === -1 || parentIndexes.length % 2 === 1 ? 'logic-box first' : 'logic-box second'}>
            <div className="logic-box-header">
                {Object.keys(options).length > 0 && logicBox[elementsName].length > 0 && (
                    <select onChange={e => changeType(e.target.value)} value={logicBox.type}>
                        {Object.keys(optionGroups).length > 0
                            ? Object.keys(optionGroups).map(label =>
                                <optgroup key={label} label={label}>
                                    {optionGroups[label].map(option =>
                                        <option key={option} value={option}>{options[option]}</option>
                                    )};
                                </optgroup>
                            )
                            : Object.keys(options).map(option =>
                                <option key={option} value={option}>{options[option]}</option>
                            )
                        }
                    </select>
                )}

                {index >= 0 && logicBox[elementsName].length > 0 &&
                <button onClick={_ => removeElement()}>
                    Delete
                </button>
                }

                {(!exactNumberOfElements || logicBox[elementsName].length < exactNumberOfElements) &&
                <button onClick={_ => addElement()}>
                    Add
                </button>}
            </div>

            {logicBox[elementsName].map((elem, idx) => {
                return <LogicBoxLeaf
                    key={idx}
                    rootLogicBox={rootLogicBox}
                    logicBox={elem}
                    elementsName={elementsName}
                    render={render}
                    add={add}
                    index={idx}
                    parentType={logicBox.type}
                    parentIndexes={index >= 0 ? [...parentIndexes, index] : parentIndexes}
                    options={options}
                    optionGroups={optionGroups}
                    optionDescriptions={optionDescriptions}
                    exactNumberOfElements={exactNumberOfElements}
                    onChange={onChange}/>;
            })}
        </div>
    );
}