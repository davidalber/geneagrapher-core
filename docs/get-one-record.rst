*******************
Get a Single Record
*******************

.. currentmodule:: geneagrapher_core.record

To get a single record, use the :func:`get_record <get_record>`
function. If you are requesting many records, consider using
:func:`get_record_inner <get_record_inner>`, which allows you to reuse
an :class:`aiohttp.ClientSession` and optionally pass a
:class:`asyncio.Semaphore` to cap maximum HTTP request concurrency.

.. autofunction:: get_record
.. autofunction:: get_record_inner

Related types
-------------
.. autoclass:: Record
   :members:
   :undoc-members:
   :member-order: bysource

.. autoclass:: Cache()
   :members:

.. autoclass:: CacheResult()
   :members:
   :undoc-members:
   :member-order: bysource

