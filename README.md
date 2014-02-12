nursery
=======

nursery aims to be a very fast deployment system - work in progress

The idea
====
The deployment system will contain a client and a server both written in python. The client will comunicate with the server sending some commands, and the server will be responsable for deploying the code on the remote instances in an asynchronous way.

Why ?
====
Why do we need another deploy system ? 
* Because this deploy system aims to be very fast. It will only deploy what files have been changed since the last deployment. 
* Because offers a clear separation between software packages and system packages administration. As a developer I'm concerned with deploying my code and I care less of system administration. The main idea is that the code changes more often then the underlying system, so it make sense to have different way of administration for each one.
