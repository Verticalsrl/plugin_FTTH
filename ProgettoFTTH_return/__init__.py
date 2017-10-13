# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ProgettoFTTH
                                 A QGIS plugin
 Importa dati catastali geometrici da file CXF
                             -------------------
        begin                : 2015-12-09
        copyright            : (C) 2015 by A.R.Gaeta/Vertical Srl
        email                : ar_gaeta@yahoo.it
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ProgettoFTTH class from file ProgettoFTTH.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .progetto_ftth import ProgettoFTTH
    return ProgettoFTTH(iface)
