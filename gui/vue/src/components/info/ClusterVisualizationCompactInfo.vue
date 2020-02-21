<template>
  <button-info popup_title="CLUSTER VISUALIZATION">
    <div class="text-left">
      <div class="h3">A Compact Representation of Meulder Hans' ILN</div>
      <p class="h5 pt-4 pl-5">
        The compact representation of a cluster allows for the display of large clusters and a comprehensive
        aggravation of nodes. The approach groups nodes base on similar link strength starting from the
        highest strength in the identity network. From the original cluster, two sub-groups of nodes can be
        identified using the link strength of 1 (black plain link) together.
      </p>

      <ul class="h5 ml-5">
        <li>Sub-group-1: Two nodes are linked with strength 1</li>
        <li>Sub-group-2: Three nodes are linked with strength 1</li>
        <li>Sub-group-3: One isolated node</li>
      </ul>

      <p class="h5 pt-4 pl-5">
        The subgroups are then interconnected using an aggregated link represented by the highest strength.
        Using such approach sub-groups and their interconnections are now clearly visible.
      </p>

      <p class="h5 pt-4 pl-5">
        Each compact node contains 3 type of information:
      </p>

      <ul class="h5 ml-5">
        <li><strong>N</strong> indicating the number of nodes aggregated by the compact node.</li>
        <li><strong>L</strong> indicating the number of links.</li>
        <li><strong>S</strong> indicating the strength of the links that enabled the aggregation.</li>
        <li>The last information (not present in this example but visible in the second compact example of
          size 35) removes a percentage of the node's color to indicate the number of missing links for the
          number of nodes aggregated
        </li>
      </ul>

      <div class="text-center pt-4">
        <img src="/static/images/1 Meulder Hans (Cluster).jpg" width="700"/>
        <p class="h5 pt-4 pl-5 font-weight-bold">
          Original Cluster
        </p>
      </div>

      <div class="text-center pt-4">
        <img src="/static/images/2 Meulder Hans (Cluster-Compact).jpg" width="700"/>
        <p class="h5 pt-4 pl-5 font-weight-bold">
          Compact Cluster
        </p>
      </div>

      <div class="h3 pt-4">Large ILN Versus its Compact Version</div>

      <p class="h5 pt-4 pl-5">
        This is an example of a bigger cluster of size 35 potentially representing <strong>Pieterss
        Grietje</strong>. The larger an ILN gets, the less comprehensive it is visually. Especially when it
        highlight a mesh topology. For this very reason, the compact version of the visual ILN is of
        importance for visual aid for validation purposes.
      </p>

      <div class="text-center pt-4">
        <img src="/static/images/1  Pieters Grietje (Cluster).jpg" width="800"/>
      </div>

      <p class="h5 pt-4 pl-5">
        This is the compact version of a cluster of size 35 potentially representing <strong>Pieterss
        Grietje</strong>. In this examople, 35 nodes are now converted into 4 compact nodes of size 25, 3, 2
        and two. The last two nodes are of size one. The compact node of size 25 is composed of 294 limks
        insted of 300. Meaning 6 links are missing.
      </p>

      <div class="text-center pt-4">
        <img src="/static/images/2  Pieters Grietje (Cluster-Compact).jpg" width="800"/>
      </div>

      <div class="h3 pt-5">Expanding a Compact Node with Double-Click</div>

      <p class="h5 pt-4 pl-5">
        For a better validation experience, each of the compact nodes can be expanded. This allows a
        detailed understanding on the type of network (START - LINE - MESH) that defines the aggragated
        node. When a compact node (sub-cluster) is double-clicked, for example the one of size 3, it is
        highlighted in red as shown in on the left side the figure below, and its expanded version is
        ploted, as shown in the right side of the figure.
      </p>

      <div class="text-center pt-4">
        <img src="/static/images/3 Meulder Hans (Cluster-Compact Selected).jpg" width="1000"/>
      </div>
    </div>
  </button-info>
</template>