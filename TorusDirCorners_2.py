# -*- coding: utf-8 -*-
# # Copyright (c) 2010 Advanced Micro Devices, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Brad Beckmann
#
# ^ ORIGINAL COPYRIGHT OF MESH TOPOLOGY WHICH WAS USED AS BASE TO THIS ^
#
# 2018
# Author: Bruno Cesar Puli Dala Rosa, bcesar.g6@gmail.com

from m5.params import *
from m5.objects import *

from BaseTopology import SimpleTopology

# Cria uma topologia Torus com 4 diretórios, um em cada canto da topologia.

class TorusDirCorners_2(SimpleTopology):
    description='TorusDirCorners_2'

    def __init__(self, controllers):
        self.nodes = controllers

    def makeTopology(self, options, network, IntLink, ExtLink, Router):
        nodes = self.nodes

        cpu_per_router = 2 # 2-ary
        num_routers = options.num_cpus / cpu_per_router
        num_rows = num_routers / 4

        ## Define as latencias associadas.
        # default values for link latency and router latency.
        # Can be over-ridden on a per link/router basis
        link_latency = options.link_latency # used by simple and garnet
        router_latency = options.router_latency # only used by garnet

        # Determina quais nodos são controladores de cache vs diretórios vs DMA
        cache_nodes = []
        dir_nodes = []
        dma_nodes = []
        for node in nodes:
            if node.type == 'L1Cache_Controller' or \
            node.type == 'L2Cache_Controller':
                cache_nodes.append(node)
            elif node.type == 'Directory_Controller':
                dir_nodes.append(node)
            elif node.type == 'DMA_Controller':
                dma_nodes.append(node)

        # O número de linhas deve ser <= ao número de roteadores e divisivel por ele.
        # O numero de caches deve ser multiplo do numero de roteadores.
        # O número de diretórios deve ser igual a 4.
        assert(num_rows > 0 and num_rows <= num_routers)
        num_columns = int(num_routers / num_rows)
        assert(num_columns * num_rows == num_routers)
        caches_per_router, remainder = divmod(len(cache_nodes), num_routers/ cpu_per_router)
        assert(remainder == 0)
        assert(len(dir_nodes) == 4)

        # Cria os roteadores (Direct type = 1 roteador para 1 node)
        routers = [Router(router_id=i, latency = router_latency) \
            for i in range(num_routers)]
        network.routers = routers

        # Contador de ID's para gerar ID's únicos das ligações.
        link_count = 0

        # Conecta cada controlador de cache ao seu roteador apropriado
        ext_links = []

        for (i, n) in enumerate(cache_nodes):
            cntrl_level, router_id = divmod(i, num_routers)
            assert(cntrl_level < caches_per_router)
            print("Conectado o node " + str(n) + " ao roteador " + str(router_id) + "\n")
            ext_links.append(ExtLink(link_id=link_count, ext_node=n,
                                    int_node=routers[router_id],
                                    latency = link_latency))
            link_count += 1

        # Conecta os diretórios aos 4 cantos
        print("Diretorio 1 ligado ao roteador " + str(0))
        ext_links.append(ExtLink(link_id=link_count, ext_node=dir_nodes[0],
                                int_node=routers[0],
                                latency = link_latency))
        link_count += 1

        print("Diretorio 2 ligado ao roteador " + str(num_columns -1))
        ext_links.append(ExtLink(link_id=link_count, ext_node=dir_nodes[1],
                                int_node=routers[num_columns - 1],
                                latency = link_latency))
        link_count += 1

        print("Diretorio 3 ligado ao roteador " + str(num_routers - num_columns))
        ext_links.append(ExtLink(link_id=link_count, ext_node=dir_nodes[2],
                                int_node=routers[num_routers - num_columns],
                                latency = link_latency))
        link_count += 1

        print("Diretorio 4 ligado ao roteador " + str(num_routers - 1))
        ext_links.append(ExtLink(link_id=link_count, ext_node=dir_nodes[3],
                                int_node=routers[num_routers - 1],
                                latency = link_latency))
        link_count += 1

        # Conecta os nodos de DMA ao roteador 0. These should only be DMA nodes.
        for (i, node) in enumerate(dma_nodes):
            assert(node.type == 'DMA_Controller')
            ext_links.append(ExtLink(link_id=link_count, ext_node=node,
                                     int_node=routers[0],
                                     latency = link_latency))

        network.ext_links = ext_links

        # Cria as conexões em Torus
        int_links = []

        # Conecta da esquerda (source) para a direita (destination)
        # East output to West input links (weight = 1)
        print("\nEast to West\n")
        for row in xrange(num_rows):
            for col in xrange(num_columns):
                if (col + 1 < num_columns):
                    east_out = col + (row * num_columns)
                    west_in = (col + 1) + (row * num_columns)
                    print("Ligou o " +  str(east_out) + " no " +  str(west_in))
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[east_out],
                                             dst_node=routers[west_in],
                                             src_outport="East",
                                             dst_inport="West",
                                             latency = link_latency,
                                             weight=1))
                    link_count += 1

                else: # O ultimo com o primeiro
                    east_out = col + (row * num_columns)
                    west_in = row * num_columns
                    print("[X] Ligou o " +  str(east_out) + " no " +  str(west_in))
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[east_out],
                                             dst_node=routers[west_in],
                                             src_outport="East",
                                             dst_inport="West",
                                             latency = link_latency,
                                             weight=1))
                    link_count += 1
            print("---")



        # Conecta da direita(source) para esquerda (destination)
        # West output to East input links (weight = 1)
        print("\nWest to East\n")
        for row in xrange(num_rows):
            for col in xrange(num_columns):
                if (col == 0 ): # O primeiro com o ultimo
                    east_in = (num_columns - 1) + (row * num_columns)
                    west_out = col + (row * num_columns)
                    print("[X] Ligou o " +  str(east_in) + " no " +  str(west_out))
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[west_out],
                                             dst_node=routers[east_in],
                                             src_outport="West",
                                             dst_inport="East",
                                             latency = link_latency,
                                             weight=1))
                    link_count += 1

                if (col + 1 < num_columns):
                    east_in = col + (row * num_columns)
                    west_out = (col + 1) + (row * num_columns)
                    print("Ligou o " +  str(east_in) + " no " +  str(west_out))
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[west_out],
                                             dst_node=routers[east_in],
                                             src_outport="West",
                                             dst_inport="East",
                                             latency = link_latency,
                                             weight=1))
                    link_count += 1
            print("---")

        print("\nNorth to south\n")
        # North output to South input links (weight = 2)
        for col in xrange(num_columns):
            for row in xrange(num_rows):
                if (row + 1 < num_rows):
                    north_out = col + (row * num_columns)
                    south_in = col + ((row + 1) * num_columns)
                    print("Ligou o " +  str(north_out) + " no " +  str(south_in))
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[north_out],
                                             dst_node=routers[south_in],
                                             src_outport="North",
                                             dst_inport="South",
                                             latency = link_latency,
                                             weight=2))
                    link_count += 1
                else: # O ultimo com o primeiro
                    north_out = col + (row * num_columns)
                    south_in = col
                    print("[X] Ligou o " +  str(north_out) + " no " +  str(south_in))
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[north_out],
                                             dst_node=routers[south_in],
                                             src_outport="North",
                                             dst_inport="South",
                                             latency = link_latency,
                                             weight=2))
                    link_count += 1
            print("---")

        # South output to North input links (weight = 2
        print("\nSouth to North\n")
        for col in xrange(num_columns):
            for row in xrange(num_rows):
                if (row == 0): # O primeiro com o ultimo
                    north_in = col + (num_columns * (num_rows -1))
                    south_out = col
                    print("[X] Ligou o " +  str(north_in) + " no " +  str(south_out))
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[south_out],
                                             dst_node=routers[north_in],
                                             src_outport="South",
                                             dst_inport="North",
                                             latency = link_latency,
                                             weight=2))
                    link_count += 1

                if (row + 1 < num_rows):
                    north_in = col + (row * num_columns)
                    south_out = col + ((row + 1) * num_columns)
                    print("Ligou o " +  str(north_in) + " no " +  str(south_out))
                    int_links.append(IntLink(link_id=link_count,
                                             src_node=routers[south_out],
                                             dst_node=routers[north_in],
                                             src_outport="South",
                                             dst_inport="North",
                                             latency = link_latency,
                                             weight=2))
                    link_count += 1
            print("---")

        network.int_links = int_links
