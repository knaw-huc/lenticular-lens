import React, {useState} from 'react';
import dataset from './dataset';
import {Property} from './Property';
import {LogicBox} from './LogicBox';

const add = () => ({hello: 'Added!'});

export default function App() {
    const logicBoxAInit: LogicBox<'conditions', { hello: string }> = {
        type: 'AND',
        conditions: [
            {
                type: 'OR',
                conditions: [{hello: 'A'}, {hello: 'B'}, {hello: 'C'}],
            }, {
                type: 'OR',
                conditions: [
                    {
                        type: 'AND',
                        conditions: [{hello: 'D'}, {hello: 'E'}],
                    },
                    {
                        type: 'AND',
                        conditions: [{hello: 'F'}, {hello: 'G'}],
                    }
                ]
            }
        ]
    };

    const logicBoxBInit: LogicBox<'elem', { hello: string }> = {
        type: 'AND',
        elem: [
            {
                type: 'OR',
                elem: [{hello: 'A'}, {hello: 'B'}],
            }, {
                type: 'OR',
                elem: [
                    {
                        type: 'AND',
                        elem: [{hello: 'D'}, {hello: 'E'}],
                    },
                    {
                        type: 'AND',
                        elem: [{hello: 'F'}, {hello: 'G'}],
                    }
                ]
            }
        ]
    };

    const [propertyA, setPropertyA] = useState(['bio_partnerList', 'saa_Person', 'pnv_hasName', 'pnv_PersonName', 'pnv_literalName']);
    const [propertyB, setPropertyB] = useState(['_inverse_saa_isInRecordList', 'pnv_PersonName', '__value__']);
    const [logicBoxA, setLogicBoxA] = useState(logicBoxAInit);
    const [logicBoxB, setLogicBoxB] = useState(logicBoxBInit);

    return (
        <div>
            <h2>Lenticular Lens</h2>

            <h3>Property</h3>

            <h4>Default</h4>
            <Property dataset={dataset} datasetId="index_op_ondertrouwregister_enriched_20200525"
                      collectionId="bio_Marriage" property={propertyA}
                      add={() => {
                      }} remove={() => {
            }}
                      onChange={(oldProp, newProp) => setPropertyA(newProp)}/>

            <h4>Read-only</h4>
            <Property dataset={dataset} datasetId="index_op_ondertrouwregister_enriched_20200525"
                      collectionId="saa_IndexOpOndertrouwregisters" property={propertyB}
                      readOnly={true}/>

            <h4>Singular</h4>
            <Property dataset={dataset} datasetId="index_op_ondertrouwregister_enriched_20200525"
                      collectionId="bio_Marriage" property={propertyA}
                      singular={true}
                      add={() => {
                      }} remove={() => {
            }}
                      onChange={(oldProp, newProp) => setPropertyA(newProp)}/>

            <h4>No deletion</h4>
            <Property dataset={dataset} datasetId="index_op_ondertrouwregister_enriched_20200525"
                      collectionId="saa_IndexOpOndertrouwregisters" property={propertyB}
                      add={() => {
                      }}
                      onChange={(oldProp, newProp) => setPropertyB(newProp)}/>

            <h4>No entity-type selection info</h4>
            <Property dataset={dataset} datasetId="index_op_ondertrouwregister_enriched_20200525"
                      collectionId="saa_IndexOpOndertrouwregisters" property={propertyB}
                      entityTypeSelectionInfo={false}
                      add={() => {
                      }} remove={() => {
            }}
                      onChange={(oldProp, newProp) => setPropertyB(newProp)}/>

            <h3>Logic Box</h3>

            <h4>Free form</h4>
            <LogicBox logicBox={logicBoxA} elementsName="conditions" add={add}
                      onChange={(oldLogicBox, newLogicBox) => setLogicBoxA(newLogicBox)}
                      render={(type: string, index: number, element: { hello: string }, add: () => void, remove: () => void) =>
                          <div>
                              <span style={{display: 'inline'}}>{element.hello}</span>

                              <button onClick={remove}>
                                  Delete
                              </button>

                              <button onClick={add}>
                                  Add
                              </button>
                          </div>
                      }/>

            <h4>Fixed size</h4>
            <LogicBox logicBox={logicBoxB} elementsName="elem" add={add} exactNumberOfElements={2}
                      onChange={(oldLogicBox, newLogicBox) => setLogicBoxB(newLogicBox)}
                      render={(type: string, index: number, element: { hello: string }, add: () => void) =>
                          <div>
                              <span style={{display: 'inline'}}>{element.hello}</span>

                              <button onClick={add}>
                                  Add
                              </button>
                          </div>
                      }/>
        </div>
    );
}
