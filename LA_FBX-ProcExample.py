########################################################################
#
#
# LA_FBX-ProcExample
# ------------------
#
# Description:
#     Simple Script to process vertex colours on an FBX Mesh based on
#     passed JSON data.
#
#    paths to file args can be absolute or relative to CWD
#
# Usage:
#    "python InputFBXFile.fbx someJSONFile.json OutputFBXFile.fbx"
#
#
#######################################################################




import os, sys, inspect, json
from FbxCommon import *
import fbx

#Display when cmdline args invalid
_SYNTAX_ = "python InputFBXFile.fbx someJSONFile.json OutputFBXFile.fbx"
_ARG_ERROR_ = -1, -1, -1




def get_CWD():
    '''
        Retun the current directory script was executed from.
        Uses inspect so as to also work correct if called indirectly 
        (such as from execfile) 
    '''
    
    filename = inspect.getframeinfo( 
                inspect.currentframe() 
            ).filename
                
                
    return os.path.dirname( 
                os.path.abspath( filename ) 
            ).replace( '\\', '/' )


    

def abs_CmdArgPath(arg):
    '''
        Standardize the absolute path to a parsed fbx or json file 
        from cmd args. 
        
        Use the current working directory if no directory was given.
    '''
    
    path = arg.replace('\\', '/')
    
    # use CWD if only a filename was given
    if '/' not in path:
        path = '%s/%s' % ( get_CWD(), path )
    
    return os.path.abspath( path ).lower().replace( '\\', '/' )
        

        
        
def assert_CmdArgs():
    '''
        Parse/Evaluate cmdline Arguments
    '''

    #valid no. args passed && file ext.
    if len( sys.argv ) < 4 or \
            not sys.argv[1].lower().endswith( '.fbx' ) \
            or not sys.argv[2].lower().endswith( '.json' ) \
            or not sys.argv[3].lower().endswith( '.fbx'):
        
        print 'Incorrect Arguments use: ', _SYNTAX_
        return _ARG_ERROR_
        

    # standardize/store paths to files for processing
    cols    = abs_CmdArgPath( sys.argv[2] )
    inFBX   = abs_CmdArgPath( sys.argv[1] )
    outFBX  = abs_CmdArgPath( sys.argv[3] )
    
    # validate passed files exist
    if not os.path.exists(inFBX):
        print 'Cannot find FBX File: ', sys.argv[1]
        return _ARG_ERROR_
    
    if not os.path.exists(cols):
        print 'Cannot find JSON File: ', sys.argv[2]
        return _ARG_ERROR_

    
    return cols, inFBX, outFBX
        
        
        
        
def parse_JSON( path ):
    '''
        parse/validate JSON file 
        
        return parsed data
    '''
    
    
    cols = {}
 
    try:
        with open( path, "r" ) as f:
            cols = json.loads( f.read() )
            
    except BaseException as e:
        print 'Error: %s, Invalid Json File ( %s )' \
            % ( e, path if isinstance(  path, str  ) else 'Missing' )
    
        
    return cols




def safeExit(lSdkManager, lExporter):
    '''
        Cleanup/Exit
    '''
    
    
    if lExporter is not None:
        lExporter.Destroy()

    if lSdkManager is not None:
        lSdkManager.Destroy()

    
    sys.exit(0)
    
    
    

def str_fromFBXColor( col ):
    '''
        parse str in form of "red,green,blue,alpha"
    '''
    
    
    return ','.join( [str(x) for x in [col.mRed, col.mGreen, col.mBlue, col.mAlpha] ] )
    
    
    
    
def process_Vertex( colorElement, vtx, JSONCols):
    '''
        Process the passed FBX mesh with JSON from:to colour adjustments
        ( at the vertex level )
        
        returns 1 if colour adjusted else 0
    '''
    

    # FBXColor
    color = colorElement.GetDirectArray().GetAt(vtx)
    
    # FBXColor in "key" format for JSON
    key = str_fromFBXColor( color )
    
    if key in JSONCols.keys():
        color.Set(*JSONCols[key])
        return 1    # increment color adjustments
    
    return 0    # no changes made




def process_FBX( root, JSONCols ):
    '''
        Process the passed FBX  mesh with JSON from:to colour adjustments
    '''
    
    adjCounter = 0
    
    for c in range(  root.GetChildCount( True )  ):
        node            = root.GetChild( c )
        mesh            = node.GetMesh()
        
        if mesh is None:
            print 'Could not find any geometry within FBX'
            return
        
        
        colorElement = mesh.GetElementVertexColor()
    
        #iterate over polys
        for poly in range ( mesh.GetPolygonCount() ):
            
            #iterate over polygon verts
            for vtx in range ( mesh.GetPolygonSize( poly ) ):        
                adjCounter += process_Vertex( colorElement, vtx, JSONCols )
                    
    return adjCounter




if __name__ == "__main__":

    # retrieve fbx/json data
    JSONFile, inFBX, outFBX   = assert_CmdArgs()
    JSONCols                  = parse_JSON( JSONFile )


    if not isinstance( JSONFile, str ) or not isinstance( inFBX , str ) \
         or not isinstance( outFBX , str ) or len(JSONCols.keys()) < 1:
        safeExit(lSdkManager, None)
        
        
    # load FBX file
    lSdkManager, lScene = InitializeSdkObjects()
    lResult             = LoadScene( lSdkManager, lScene, inFBX )
    

    if not lResult:
        print("\n\nAn error occurred while loading the scene...")
        safeExit(lSdkManager, None)
    
    
    # iterate over mesh in scene
    adjCounter = process_FBX( lScene.GetRootNode(), JSONCols )
                    
    if adjCounter < 1:
        print 'No Changes Were Processed.'
        safeExit(lSdkManager, None)
        
        
    #export processed FBX  file
    lExporter = FbxExporter.Create( lSdkManager, "" )
    lExportStatus = lExporter.Initialize( outFBX, -1, lSdkManager.GetIOSettings() )
    
    if not lExportStatus:
        print "Call to FbxExporter::Initialize() failed.\n"
        safeExit(lSdkManager, lExporter)


    print 'Exported %s changes: %s' % ( adjCounter, outFBX )
    safeExit(lSdkManager, lExporter)
    
    
    
    